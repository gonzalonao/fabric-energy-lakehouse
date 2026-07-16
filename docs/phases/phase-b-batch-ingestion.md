# Phase B — Batch ingestion

**Progress:** tracked per run in [track-a-progress.md](track-a-progress.md) · [track-b-progress.md](track-b-progress.md)
**Days:** D2–D3 · **Plan:** [P1 §Phase B](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phase A ✅

## Outcome (done criteria)

- Backfill 2023-01 → now loaded into Bronze Files for all three indicators.
- Daily incremental run picks up **only new dates** — proven with run-history
      screenshots (watermark before/after).
- A run killed mid-flight re-runs idempotently (no duplicate/partial data).
- Daily schedule active; failure alert wired.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Pipeline split | `pl_ingest_ree` (pure, parameterized single fetch) + `pl_backfill_ree` (ForEach over month-chunks) + `pl_ingest_daily` (watermark-driven wrapper, scheduled) | The core stays idempotent and testable; backfill and daily are thin callers — this is the answer to the "incremental watermark design" interview drill |
| Idempotency mechanism | Deterministic file path per (indicator, month); Copy activity **overwrites** | Re-running any slice rewrites the same file — no dedup logic needed in Bronze |
| Watermark store | Delta table `bronze.ctl_watermark` (`indicator, last_end, updated_at`) in `lh_energy`; **read** via Lookup on the SQL endpoint, **written** by notebook `nb_update_watermark` | SQL analytics endpoint is read-only, so writes must go through Spark |
| Watermark update timing | Only **after** a successful copy, never before | A failed run leaves the watermark untouched → next run retries the same window |
| API politeness | ForEach loops run **sequential** (no parallel hammering), month-sized requests | REE fair-use: no redundant requests (see `wiki/learning/esios-api-usage.md`); tokenless API but same spirit |
| Env config | Variable library `vl_energy` for alert email + default backfill start | Small honest use now; Phase F extends it with dev/prod value sets |
| Alert recipient | `v_alert_email` = `gonzalonao@gmail.com` (personal, not the student tenant address) | Variable-library value sets are **committed as code** to a public repo, so the value is a deliberate choice. This address is already in the repo's commit history (so no new exposure), survives the trial's expiry, and is the one Track B uses on the own tenant. See Gotchas 2026-07-14 |
| Failure alert | Office 365 Outlook activity on-fail | Simplest wiring; if the trial account has no Exchange license, log it here and swap for a Teams activity |

## REE API reference (`apidatos.ree.es`, tokenless)

Base URL `https://apidatos.ree.es` · GET · `Accept: application/json` · no auth.
Query params: `start_date=YYYY-MM-DDTHH:mm&end_date=YYYY-MM-DDTHH:mm&time_trunc=<grain>`.
Keep every request ≤ 1 calendar month (hourly series reject long ranges).

| Indicator (our name) | Path | `time_trunc` | Grain |
|---|---|---|---|
| `demanda_evolucion` | `/es/datos/demanda/evolucion` | `day` | Daily demand (MW) |
| `generacion_estructura` | `/es/datos/generacion/estructura-generacion` | `day` | Daily generation by technology |
| `precios_mercados` | `/es/datos/mercados/precios-mercados-tiempo-real` | `hour` | Hourly market price (€/MWh) |

Smoke test (PowerShell):
`Invoke-RestMethod "https://apidatos.ree.es/es/datos/demanda/evolucion?start_date=2024-01-01T00:00&end_date=2024-01-31T23:59&time_trunc=day"`

Bronze layout in `lh_energy` → Files:
`raw/<indicator>/<yyyy>/<MM>/<indicator>_<yyyyMM>.json`

~~Stretch: PVPC via `api.esios.ree.es`.~~ **Dropped 2026-07-14** — `precios_mercados`
already returns PVPC tokenless (see Gotchas). No ESIOS token is needed in P1.

## Steps

### B1 `[YOU]` Learn first (~1–2 h, timeboxed)

Read in order (the Data Factory ToC was reorganized in 2026 — these are the current pages;
the `/fabric/data-factory/` landing ToC does **not** list them):

1. [Pipeline overview](https://learn.microsoft.com/fabric/data-factory/pipeline-overview)
2. [Activity overview](https://learn.microsoft.com/fabric/data-factory/activity-overview) —
   the three families: data movement / transformation / control flow.
3. [Copy activity in pipelines](https://learn.microsoft.com/fabric/data-factory/copy-data-activity)
4. [Web activity](https://learn.microsoft.com/fabric/data-factory/web-activity) — read it for
   what it **lacks**: no destination.
5. [Parameters](https://learn.microsoft.com/fabric/data-factory/parameters)
6. [Expressions and functions](https://learn.microsoft.com/fabric/data-factory/expression-language)
   — `@concat`, `@formatDateTime`, `@item()`, string interpolation `@{...}`. The page that
   matters most for actually building B3.
7. [ForEach activity](https://learn.microsoft.com/fabric/data-factory/foreach-activity) — note
   the **Sequential** toggle.
8. [Variable library overview](https://learn.microsoft.com/fabric/cicd/variable-library/variable-library-overview)

Drill answers to hold:

- **Copy vs Web** — **Copy** = connector-based data movement that writes to a destination
      (files/tables); **Web** = control-flow REST call whose (size-limited) response stays
      inside the pipeline's run state, unpersisted. We use Copy with a REST source because the
      payload must land in Files.
- **Copy job vs Copy activity** — [decision guide](https://learn.microsoft.com/fabric/data-factory/decision-guide-data-movement).
      MS recommends **Copy job** as the default for Bronze/raw ingestion; it's a standalone item
      with **native watermark-based incremental copy and CDC**, which Copy activity lacks (with
      Copy activity *you* track last-run state — which is exactly what B4–B6 build).
      **We use Copy activity anyway** because (a) our unit of work is a **URL**, not a queryable
      table — the date window is baked into the URL string, so there is nothing for Copy job to
      watermark against; (b) we need ForEach + Invoke-pipeline composition and On-fail branching;
      (c) hand-building the watermark is an explicit interview drill. Be able to say that a SQL
      source would likely have made Copy job the better call — chosen, not defaulted.

Hands-on (the part that makes it stick): build a throwaway `pl_scratch` pipeline — drag a Copy
activity (see the REST source + the *separate* folder and file-name destination boxes), drag a
Web activity (see it has no destination at all), add a String parameter and resolve it via
**Add dynamic content**, and pull out the red **On fail** handle. **Delete it; don't commit it.**

### B1.5 `[CLAUDE]` 🎓 Understanding check — ingestion & watermarks

- Claude diagrams the `pl_ingest_ree` → backfill/daily topology (Web/Copy source,
      Bronze Files layout, watermark read via Lookup / write via notebook) and quizzes
      Gonzalo (`AskUserQuestion`) on the drill answers: **Copy vs Web activity**, why the
      **watermark is written only after a successful copy**, and what makes a re-run
      **idempotent** here (deterministic path + overwrite). Pull a MS Learn source if a
      point is fuzzy.
- Record weak spots for the Phase G drills.

### B2 `[YOU]` Variable library `vl_energy`

- `ws-energy-dev` root → **+ New item** → **Variable library** → `vl_energy`.
- Variables: `v_alert_email` = your email · `v_backfill_start` = `2023-01-01`.
- Commit via Source control (`feat(ingest): add variable library`).

### B3 `[YOU]` Core pipeline `pl_ingest_ree`

- In folder `orchestration` → **+ New item** → **Data pipeline** → `pl_ingest_ree`.
- Canvas background → **Parameters** tab → add (all String):
      `p_indicator_path` (e.g. `demanda/evolucion`), `p_indicator_name`
      (e.g. `demanda_evolucion`), `p_time_trunc` (`day`/`hour`),
      `p_start` (`YYYY-MM-DDTHH:mm`), `p_end` (same format).
- Add **Copy data** activity `cp_fetch_json`:
  - Source → Connection → **REST**, new connection `conn_ree_apidatos`:
    Base URL `https://apidatos.ree.es`, Authentication **Anonymous**.
  - Relative URL → dynamic content:
    `@concat('/es/datos/', pipeline().parameters.p_indicator_path, '?start_date=', pipeline().parameters.p_start, '&end_date=', pipeline().parameters.p_end, '&time_trunc=', pipeline().parameters.p_time_trunc)`
  - Request method GET.
  - Destination → **Lakehouse** `lh_energy` → **Files** · File format **JSON**:
    - Folder: `@concat('raw/', pipeline().parameters.p_indicator_name, '/', formatDateTime(pipeline().parameters.p_start, 'yyyy'), '/', formatDateTime(pipeline().parameters.p_start, 'MM'))`
    - File name: `@concat(pipeline().parameters.p_indicator_name, '_', formatDateTime(pipeline().parameters.p_start, 'yyyyMM'), '.json')`
  - General tab → **Retry 3**, retry interval 60 s.
- Add **Office 365 Outlook** activity `mail_failure`, connected from `cp_fetch_json`
      with an **On fail** (red) dependency. To: `v_alert_email` (expression builder →
      Library variables). Subject: include `@{pipeline().parameters.p_indicator_name}`
      and `@{pipeline().RunId}`.
- Test run: canvas **Run** with `demanda/evolucion` · `demanda_evolucion` · `day` ·
      `2024-01-01T00:00` · `2024-01-31T23:59`. Verify the JSON lands at
      `raw/demanda_evolucion/2024/01/demanda_evolucion_202401.json` (lakehouse Files view).
- Run it **again** with identical params → same single file, overwritten (check the
      modified timestamp changed, file count didn't). That's the idempotency proof at
      the unit level — screenshot both.
- Commit (`feat(ingest): core parameterized REE ingest pipeline`).

### B4 `[YOU]` → `[CLAUDE]` Watermark + chunking notebooks (hybrid flow)

The standard flow for any new notebook from here on: **you create the empty shell in
Fabric** (so it gets valid `.platform` metadata), **Claude writes the code in the repo**,
you pull it back.

- `[YOU]` In folder `orchestration`, create two empty notebooks, attach `lh_energy`
      to both, commit: `nb_update_watermark`, `nb_gen_backfill_chunks`.
- `[CLAUDE]` Pull; write both notebooks in the Git `.py` format on a
      `feature/ingest-notebooks` branch; PR → `develop`; merge:
  - `nb_update_watermark` — params `p_indicator`, `p_new_end`; `MERGE` upsert into
    `bronze.ctl_watermark` (creates the table on first run); typed helper logic, no
    prints, follows `.claude/rules/python.md` where notebook-practical.
  - `nb_gen_backfill_chunks` — params `p_from`, `p_to`; emits via
    `notebookutils.notebook.exit(...)` a JSON array of
    `{indicator_path, indicator_name, time_trunc, start, end}` for every
    (indicator × month) chunk, all three indicators hardcoded in one config dict.
- `[YOU]` **Source control → Update all**; open both notebooks and run
      `nb_update_watermark` once manually (any indicator, e.g. `demanda_evolucion` /
      `2022-12-31T23:59`) to create `bronze.ctl_watermark`; verify the table appears
      under Tables → bronze.

### B5 `[YOU]` Backfill pipeline `pl_backfill_ree`

- New data pipeline in `orchestration` → `pl_backfill_ree`; parameters `p_from`
      (default from `v_backfill_start`), `p_to`.
- **Notebook** activity `nb_chunks` → runs `nb_gen_backfill_chunks`, passing
      `p_from`/`p_to` as base parameters.
- **ForEach** `fe_chunks` → Items:
      `@json(activity('nb_chunks').output.result.exitValue)` → **Sequential = ON**
      (REE politeness — see Decisions).
  - Inside: **Invoke pipeline** → `pl_ingest_ree`, mapping all five parameters from
    `@item()`.
- After ForEach (On success): **Notebook** activity → `nb_update_watermark` per
      indicator set to `p_to` — simplest: three parallel notebook activities, one per
      indicator (explicit beats clever here).
- Commit (`feat(ingest): month-chunked backfill pipeline`).

### B6 `[YOU]` Daily pipeline `pl_ingest_daily`

- New data pipeline in `orchestration` → `pl_ingest_daily`, no required params.
- **ForEach** over the three indicators (pipeline array variable or the same config
      via `nb_gen_backfill_chunks` pattern — keep it simple: array parameter with
      3 JSON objects, Sequential = ON). Inside, per indicator:
  - **Lookup** `lkp_watermark` → connection: `lh_energy` **SQL analytics endpoint** →
    query: `SELECT last_end FROM bronze.ctl_watermark WHERE indicator = '<name>'`
    (dynamic via `@item()`).
  - **Invoke pipeline** `pl_ingest_ree` with `p_start` = watermark value,
    `p_end` = yesterday 23:59:
    `@concat(formatDateTime(addDays(utcNow(), -1), 'yyyy-MM-dd'), 'T23:59')`.
  - **Notebook** `nb_update_watermark` (On success) → sets watermark to that `p_end`.
- Commit (`feat(ingest): watermark-driven daily incremental pipeline`).

### B7 `[YOU]` Run the backfill

- Run `pl_backfill_ree` with `p_from` = `2023-01-01`, `p_to` = yesterday.
      ~43 months × 3 indicators ≈ 130 sequential ingest runs — expect it to take a
      while; watch the first few in **Monitor**, then let it finish.
- Verify: Files tree shows `raw/<indicator>/2023/01/ … /2026/07/` for all three;
      spot-open one 2023 and one 2026 file.
- Screenshot the green run in Monitor + the Files tree.

### B8 `[YOU]` Prove incremental + idempotent (the money screenshots)

- Run `pl_ingest_daily` manually → it should fetch only the window
      `watermark → yesterday` (small/no-op). Screenshot run history showing the tiny
      incremental run right after the big backfill.
- Run it again immediately → near-zero window, same files overwritten, no new
      paths. Screenshot.
- Kill-test: start `pl_backfill_ree` for a short range (e.g. one month), **Cancel**
      it mid-run from Monitor, re-run same params → completes green, file set identical.
      Screenshot cancelled + rerun pair.

### B9 `[YOU]` Schedule + final commit

- `pl_ingest_daily` → **Run → Schedule**: daily **08:00**, time zone
      **Europe/Madrid** (previous day's data is complete by then), start date = tomorrow,
      end date = 2026-07-31 (trial end).
- Next morning: verify the scheduled run is green in Monitor (this is the
      "two days straight" evidence Phase D formalizes).
- Source control → commit anything pending
      (`feat(ingest): schedule daily incremental run`).

### B10 `[CLAUDE]` Review + evidence + docs

- Pull `develop`; review the three `*.DataPipeline/pipeline-content.json`
      definitions (naming, retry settings, no secrets/emails hardcoded where a library
      variable should be).
- Move screenshots into `docs/evidence/phase-b/`, normalize names, commit.
- Update this file: tick done-criteria, Status ✅, session log; note actual backfill
      duration + any API quirks under Gotchas (feeds the README + interview drills).
- 📣 **Portfolio (capture, not publish):** stash the money screenshots (incremental
      vs backfill run history, idempotent re-run) and the backfill duration for the
      portfolio entry — they land in the write-up at the Phase C 📣 checkpoint. No entry
      edit yet; just make sure the assets are named and kept.

## Gotchas & deviations

**2026-07-14 — API probed before building (all three endpoints, Jan 2024, anonymous).**
All return `200` with a 1-calendar-month window and the documented `time_trunc`. Payload
shape is JSON:API — the series live in `included[]`, each with
`attributes.title` / `attributes.values[]` (`{value, percentage, datetime}`):

| Indicator | `time_trunc` | Series returned | Points (Jan 2024) |
|---|---|---|---|
| `demanda_evolucion` | `day` | 1 — *Demanda* | 31 |
| `generacion_estructura` | `day` | **16** | 496 |
| `precios_mercados` | `hour` | **2** — *PVPC*, *Precio mercado spot* | 1488 |

Two consequences:

- **PVPC comes free.** `precios-mercados-tiempo-real` already carries PVPC next to the
  spot price. The ESIOS stretch goal existed to fetch PVPC behind a token — **it is now
  redundant**, and no ESIOS token is needed anywhere in P1. Silver will model price as a
  long fact with a `price_type` dimension (`pvpc` / `spot`) rather than one price column.
- **`generacion_estructura` contains an aggregate row.** The 16th series is
  *Generación total* — a total sitting in the same array as the 15 real technologies.
  **Summing the array naively double-counts.** Silver must drop it (and Phase C's DQ gate
  should assert `sum(technologies) ≈ Generación total` — the aggregate becomes a free
  cross-check rather than a bug).

**2026-07-14 — PII in a public repo: variable-library values are code.** A variable library
serializes its **value sets into Git** (MS: variables "managed as code, integrated with Git"),
so `v_alert_email` is published, not configuration-in-a-vault. Checked what's already exposed
before choosing a value — **both addresses are already in this repo's commit history**:
`GLOPEZC443@alumnos.imf.com` (Fabric commits **as the signed-in tenant user** — present since
the first sync, `ca6ccdd`) and `gonzalonao@gmail.com` (local commits). So the A5 screenshot
redaction closed a window that was already open via commit metadata.

**Decided:** use `gonzalonao@gmail.com` (no new exposure, survives the trial, matches Track B)
and **leave the history alone** — commit emails are ordinary public-repo metadata, not
credentials, and rewriting history on a repo Fabric is Git-bound to (force-push × 2 remotes +
workspace re-sync) risks the binding for negligible gain. **Track B note:** Fabric will commit
as *that* tenant's identity; the tenant address is set by the identity, not by git config.

**Real lesson for the write-up:** the privacy boundary in Fabric ALM isn't the variable
library — it's the **connection**. Variables are published; secrets belong in a connection's
credential store (or Key Vault), never in a value set. This is why the ESIOS token would never
have gone in `vl_energy` even if we'd kept that stretch goal.

*(append further as encountered — remaining suspects: Outlook activity licensing on the
student tenant, Variable-library expression syntax in preview)*

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
