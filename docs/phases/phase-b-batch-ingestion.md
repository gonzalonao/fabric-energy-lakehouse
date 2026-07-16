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
| Watermark store | Delta table `bronze.ctl_watermark` (`indicator, last_end, updated_at`) in `lh_energy`; **read and written by Spark notebooks** (`nb_gen_chunks` reads, `nb_update_watermark` writes) | **Revised 2026-07-16** — originally "read via Lookup on the SQL endpoint". T-SQL Query mode is unusable with the connection Fabric provides (see Gotchas), and the notebook approach turned out better on the merits. The endpoint's read-only nature is still the reason **writes** go through Spark; it gets demonstrated at **C7** |
| Work-list generation | **One** notebook `nb_gen_chunks` with `p_mode` = `backfill` \| `daily` | Generating a work list is one responsibility; the mode only decides where each start date comes from (`p_from` vs each indicator's own `last_end`). Keeps `INDICATORS` and `month_windows` in exactly one place, and makes both pipelines the same shape |
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
| `precios_mercados` | `/es/datos/mercados/precios-mercados-tiempo-real` | `hour` | Market price (€/MWh) — **two series at two different grains**, see Gotchas 2026-07-16. *Not* uniformly hourly |

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
  - **Mapping tab — leave it EMPTY. Never click *Import schema*.** Empty mapping = default
    schema mapping = the REST response is written **as-is**. Defining a mapping makes Copy
    parse and re-serialize the payload, so Bronze would hold *Fabric's interpretation* of
    REE's JSON instead of what REE sent — which defeats "raw and replayable".
    (Verified 2026-07-14: `b3-bronze-json-raw.png`.)
- Add **Office 365 Outlook** activity `mail_failure`, connected from `cp_fetch_json`
      with an **On fail** (red) dependency. To: `v_alert_email` (expression builder →
      Library variables) — the UI emits
      **`@pipeline().libraryVariables.vl_energy_v_alert_email`**, i.e. the reference is
      flattened to `libraryVariables.<library>_<variable>`, not a nested path. Subject:
      include `@{pipeline().parameters.p_indicator_name}` and `@{pipeline().RunId}` (the Run
      ID is what makes the alert actionable — it's what you paste into Monitor).
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
    `@item()`. **Use the new *Invoke pipeline*, not *Invoke pipeline (Legacy)*** — see
    Gotchas 2026-07-16. It needs a connection (`conn_fabric_pipelines`, **Organizational
    account**); Legacy needs none but can only monitor the *parent* pipeline, which is
    unacceptable when B7 fires 129 child runs at a WAF-fronted API. Set **Wait on
    completion = ON**, or `Sequential` is meaningless (the loop would fire and move on).
- After ForEach (On success): **Notebook** activity → `nb_update_watermark` per
      indicator set to `p_to` — simplest: three parallel notebook activities, one per
      indicator (explicit beats clever here).
- Commit (`feat(ingest): month-chunked backfill pipeline`).

### B6 `[YOU]` Daily pipeline `pl_ingest_daily`

**Redesigned 2026-07-16** — the Lookup-on-SQL-endpoint design is abandoned (see Gotchas); the
daily pipeline is now the **same shape as the backfill**, driven by `nb_gen_chunks` in `daily`
mode. This also fixes a latent bug in the original design: it issued **one** request per
indicator for `watermark → yesterday`, so any outage longer than a calendar month produced a
window the API rejects — and since a failed run (correctly) never advances the watermark, the
daily pipeline could **never catch up without manual intervention**. Chunking the daily window
by month removes that trap.

- New data pipeline in `orchestration` → `pl_ingest_daily`, **no parameters**.
- **Notebook** `nb_chunks` → `nb_gen_chunks`, base parameter `p_mode` = `daily` (literal).
      It reads each indicator's own `last_end` from `bronze.ctl_watermark`, so a lagging
      indicator resumes from its own position rather than a shared one.
- **ForEach** `fe_chunks` → Items `@json(activity('nb_chunks').output.result.exitValue)`,
      **Sequential = ON**. Inside: **Invoke pipeline** → `pl_ingest_ree`, all five parameters
      from `@item()` (identical to B5).
- **Notebook** `nb_wm_update` (On success from `fe_chunks`) → `nb_update_watermark`.
      Three parallel activities, one per indicator, `p_new_end` = yesterday 23:59:
      `@concat(formatDateTime(addDays(utcNow(), -1), 'yyyy-MM-dd'), 'T23:59')`.
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

**2026-07-14 — REST source ships a non-empty pagination default.** B3 said "leave pagination
rules empty"; they aren't empty by default. Fabric pre-populates **`RFC5988 = True`**, which
makes Copy follow `Link: rel=next` headers and **concatenate every page into the single output
file** — silently breaking the one-request-one-file contract Bronze depends on.

Probed the API: **REE returns no `Link` header**, so the rule is inert and we left it at the
default. Cross-check that the landing is byte-faithful: raw response = **2946 bytes**, landed
file = **2 KB**. *If a future source does emit `Link` headers, set `supportRFC5988 = False`
explicitly, or Bronze stops being raw without any error.*

**2026-07-14 — REE sits behind an Imperva WAF** (`X-CDN: Imperva` in the response headers).
This upgrades `Sequential = ON` from politeness to **self-preservation**: B7 fires ~130 requests
at a WAF-fronted public endpoint, and parallel bursts are what bot protection exists to stop.
Watch the first few B7 iterations for `403`s rather than assuming a green first run means the
whole backfill is safe.

**2026-07-14 — Variable-library reference syntax** (recorded because the docs don't spell it
out): the expression builder emits `@pipeline().libraryVariables.vl_energy_v_alert_email` —
library and variable names are **flattened with an underscore**, not a nested path.

**2026-07-16 — Outlook activity worked on the student tenant.** The anticipated Exchange
licensing blocker (see Decisions) did not materialize; no Teams fallback needed. Track B
inherits the simpler path.

**2026-07-16 — B3's committed definition bakes in two dev GUIDs → a hard Phase F requirement.**
Reviewing `pl_ingest_ree.DataPipeline/pipeline-content.json` after the commit:

```json
"artifactId": "8bdb6c16-94fa-9379-43ad-836e6cabfc1b",   // dev's lh_energy
"connection": "3cc793f5-7a71-4133-8102-f88cadcd4458"     // dev's REST connection
```

Fabric writes these itself; there is no UI option to make them symbolic. Deployed verbatim to
prod, the pipeline would write into the **dev** lakehouse via the **dev** connection **without
erroring** — the GUIDs resolve, just to the wrong tenant's objects. **`parameter.yml` must
substitute both** (`lh_energy` artifactId and the `conn_ree_apidatos` connection id), and both
change again on Track B's tenant. Every pipeline added in B5/B6 inherits the same issue —
collect the GUIDs as they appear rather than archaeologically at F2.

Note the contrast: `v_alert_email` is *not* hardcoded (it's a `libraryVariables` reference).
The variable library parameterizes values **we** chose to control; `parameter.yml` covers the
GUIDs Fabric bakes in regardless.

**2026-07-16 — ⚠️ Fabric writes the same lakehouse GUID in TWO different encodings.**
`lh_energy`'s `logicalId` is `8bdb6c16-94fa-9379-43ad-836e6cabfc1b` (see its `.platform`).
That exact string appears in the **pipeline** definition. The **notebook** metadata references
the same lakehouse as `6cabfc1b-836e-43ad-9379-94fa8bdb6c16` — the *same GUID with its six
segments in reverse order* (verified: identical character multiset, exact chunk reversal; the
odds of coincidence are nil).

| Item type | Field | Encoding of `lh_energy` |
|---|---|---|
| Data pipeline | `artifactId` | `8bdb6c16-94fa-9379-43ad-836e6cabfc1b` (= `logicalId`) |
| Notebook | `default_lakehouse` / `known_lakehouses[].id` | `6cabfc1b-836e-43ad-9379-94fa8bdb6c16` (reversed) |

**Phase F consequence — this is the dangerous one.** A `parameter.yml` find/replace on the dev
lakehouse GUID written in the pipeline's form **matches every pipeline and silently misses every
notebook**. The deploy would succeed, prod's pipelines would correctly target prod's lakehouse,
and prod's notebooks would keep writing into **dev**. A half-migrated deployment is worse than a
failed one — it produces plausible-looking output from the wrong place. **`parameter.yml` must
cover both string forms**, and F2's ID collection must record both.

**2026-07-16 — ⚠️ `time_trunc=hour` is NOT honoured for the spot price, and the grain changes
mid-history.** Found by feeding a *generated* B4 chunk to the live API and checking the point
count (15 days × 24 h × 2 series should be 720; it returned **1800**).

`precios-mercados-tiempo-real` returns **two series at two different grains**, and one of them
switched grain **on 2025-01-01** (Spain's move to 15-minute market time units):

| Window | PVPC | Precio mercado spot |
|---|---|---|
| Jan 2024 | 744 pts · 60 min | 744 pts · **60 min** |
| **2024-12** | 60 min | **60 min** ← last hourly month |
| **2025-01** | 60 min | **15 min** ← cutover |
| Sep 2025 | 720 pts · 60 min | 2880 pts · **15 min** |

**Our backfill range (2023-01 → now) straddles the cutover**, so the price data is hourly for
its first two years and quarter-hourly thereafter — in the same table, from the same endpoint,
with the same `time_trunc=hour` request. The API parameter is advisory for this series.

**Consequences for Phase C (the price model must be designed for this, not patched later):**
- A `fact_price` at hourly grain is **wrong from 2025-01 onward** — it would silently average or
  quadruple-count. Model price as a long fact: `price_type` (`pvpc` | `spot`), `period_start`
  (UTC), **`period_minutes`** (60 | 15), `value`. The grain becomes data, not an assumption.
- The **DQ gate** should assert the point count per window against the expected count *derived
  from the observed grain*, and flag a grain change rather than absorb it.

**2026-07-16 — DST is physically present in the data; UTC normalization is load-bearing.**
Timestamps are **Europe/Madrid local with offset**, and the transition months prove it:

| Month | Actual | Expected | Delta | Cause |
|---|---|---|---|---|
| 2024-03 | 743 | 744 (31×24) | **−1** | spring-forward: 02:00 never happens |
| 2024-10 | 745 | 744 | **+1** | fall-back: 02:00 happens twice |
| 2025-03 | 2972 | 2976 (31×96) | **−4** | spring-forward, quarter-hours |
| 2025-10 | 2980 | 2976 | **+4** | fall-back |
| 2025-05 | 2976 | 2976 | 0 | no transition |

Transition months carry **both `+01:00` and `+02:00`** offsets; normal months carry one. So the
Silver UTC rule is not box-ticking: without it, one hour each October **duplicates** (a real
dedup-on-business-key hazard, since local timestamp alone is not unique) and one hour each March
is **missing** (a gap that is correct and must not be flagged as an error). A DQ rule of "every
day has 24 rows" would be wrong twice a year.

**2026-07-16 — there are TWO Invoke pipeline activities; the new one requires a connection.**
B5 failed to save with *"inv_ingest requires a connection"*. Fabric ships both:

| | **Invoke pipeline (Legacy)** | **Invoke pipeline** (new) |
|---|---|---|
| Connection | none | **required** (token in Fabric's credential store) |
| Scope | same workspace only | cross-workspace, ADF, Synapse |
| Monitoring | **parent pipeline only** | **child pipelines too** |
| Auth kinds | — | Organizational account · service principal · workspace identity |

**Chose the new activity** despite the extra connection: B7 fires **129 child runs** at a
WAF-fronted API, and B8's evidence *is* run history. Legacy would surface a failed parent with
no drill-down — unacceptable for diagnosing a 403 at iteration ~30.

**Auth = Organizational account.** Service principal and workspace identity both require the
tenant setting *"Service principals can call Fabric public APIs"*, which needs admin rights we
don't have on the student tenant (same wall as A5's GitHub provider). **Track B should revisit
this** — on the own tenant, workspace identity is the better answer.

**Phase F consequence — the same lesson as M3 from a new angle: *definitions deploy,
connections don't*.** `conn_fabric_pipelines` stores **Gonzalo's user token** and lives in the
**tenant**, not in Git; the definition references it by GUID only. So the repo still holds no
credentials (the B2 boundary holds), but prod cannot inherit this connection: it must have its
own, authenticated as something that isn't a person. That makes **two** connection GUIDs for
`parameter.yml` (`conn_ree_apidatos`, `conn_fabric_pipelines`) on top of the lakehouse GUIDs —
and it means the backfill currently runs **as Gonzalo**, which is fine in dev and wrong in prod.

**2026-07-16 — the SQL analytics endpoint is a *mode*, not a connection.** B6 said to pick the
"`lh_energy` SQL analytics endpoint" from the Lookup's connection dropdown. **No such entry
exists** — the OneLake catalog lists only `lh_energy` as a Lakehouse. The endpoint is reached by
selecting the lakehouse and then choosing **Root folder = Tables** → **Use query = T-SQL Query
(Preview)**. Documented caveat: T-SQL Query mode is *"supported only when you read the Lakehouse
via the connection set up in Manage connections and gateways"*, so the inline catalog picker may
not expose it; fallback is an explicit **SQL Server** connection to the endpoint's connection
string (Lakehouse → ⚙ Settings → SQL analytics endpoint), at the cost of a third connection to
parameterize.

**Why Table mode is a dead end here** (worth knowing — it looks like the simpler option):
`Table` mode reads `ctl_watermark` wholesale with no `WHERE`, returning all three rows, and
pipeline expressions have **no array-filter function**. A Filter activity doesn't help either —
its `@item()` shadows the enclosing ForEach's. The `WHERE` must therefore execute at the source,
which means the SQL endpoint. Reinforces **M5**: the endpoint reads (filters, returns) and never
writes; the watermark write still goes through Spark.

**2026-07-16 — ⛔ T-SQL Query (Preview) is unusable with the Lakehouse connection Fabric gives
you; the Lookup design was abandoned.** Selecting `lh_energy` → *Root folder: Tables* →
*Use query: T-SQL Query (Preview)* returns:

> *"Please update the connection to utilize the available authentication kind to enable query mode"*

The connection's **Authentication method offers only OAuth 2.0** — which *is* Entra auth, so
there is nothing to change. (The "Organizational" option visible in the dialog is under **Privacy
level**, a Power Query data-privacy setting, unrelated to authentication.) The documented
constraint — *"supported only when you read the Lakehouse via the connection set up in Manage
connections and gateways"* — cannot be satisfied with the connection the OneLake catalog picker
produces. Three attempts, then stopped.

**Decision: Option B — the watermark is read by a Spark notebook** (`nb_gen_chunks` in `daily`
mode) instead of a Lookup. Not a workaround; better on the merits:

| | Lookup + SQL Server connection (Option A) | Notebook (chosen) |
|---|---|---|
| Phase F connections | **3** | **2** (unchanged) |
| `INDICATORS` config | duplicated (notebook + pipeline JSON) | **one place, in Python** |
| Pipeline shape | daily ≠ backfill | **identical** |
| Spark session cost | already paid — `nb_update_watermark` is a notebook | already paid |
| Logic testability | SQL inside a pipeline expression | **testable Python** |

The Spark-cost objection — the main argument for the Lookup — was **wrong**: `pl_ingest_daily`
already runs `nb_update_watermark`, so a Spark session start was always in the daily critical
path.

**What we give up:** the SQL endpoint no longer appears in the daily architecture, so the
read/write asymmetry (**M5**) isn't visible there. It is still demonstrated at **C7** (gold
SQL proofs), which was already planned — so the lesson moves rather than disappears. The
endpoint's read-only nature remains the reason `nb_update_watermark` exists at all.

*(append further as encountered)*

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
