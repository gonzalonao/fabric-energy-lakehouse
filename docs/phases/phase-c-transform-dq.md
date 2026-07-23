# Phase C — Transform & data quality

**Progress:** tracked per run in [track-a-progress.md](track-a-progress.md) · [track-b-progress.md](track-b-progress.md)
**Days:** D3–D5 · **Plan:** [P1 §Phase C](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phase B ✅ (backfill loaded)

## Outcome (done criteria)

- Silver Delta tables: typed, deduped, UTC-normalized; malformed rows quarantined.
- DQ gate: a **deliberately corrupted Bronze file fails the run with a clear DQ
      error** (screenshot), and the same run goes green after cleanup.
- Gold star schema built: `dim_date`, `dim_technology`, `dim_indicator`,
      `fact_demand_daily`, `fact_generation_daily`, `fact_price_hourly`.
- ≥1 materialized lake view on Gold + honest README paragraph (MLV vs notebook table).
- Gold queries correctly from the SQL analytics endpoint — `.sql` proofs in repo.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Helper-code packaging | `src/` becomes an installable package **`energy_lakehouse`** (hatchling, `pyproject.toml`); built as a wheel and attached to a Fabric **Environment** `env_energy` set as the workspace default | Typed, `mypy --strict`, pytest-able locally — the "typed helper modules, notebooks stay thin" claim made real; notebooks just import it |
| Silver notebook shape | **One parameterized notebook** `nb_bronze_to_silver` (param `p_indicator`); per-indicator parse logic lives in `energy_lakehouse.parsers` | 3 near-identical notebooks would drift; the parser module is unit-tested locally |
| Natural keys (dedup) | demand: `date` · generation: `(date, technology)` · prices: `(datetime_utc, series)` | The prices endpoint returns multiple series (spot + PVPC) per hour |
| Quarantine | Delta table `silver.quarantine` (raw record as string, indicator, reason, load timestamp) — never dropped silently | "Quarantine, don't discard" is the recruiter-visible DQ posture |
| DQ results | Delta table **`ops.dq_results`** (new `ops` schema). `bronze.ctl_watermark` stays where Phase B put it — migrate to `ops` only if it ever bothers us | Control data isn't bronze/silver/gold; starting the `ops` convention now |
| DQ gate behavior | `nb_dq_gate` (param `p_stage`) runs all checks for the stage, writes every result to `ops.dq_results`, then **raises** if any FAIL → pipeline fails | Write-then-raise: the failure is diagnosable from the table, not just the stderr |
| Gold build | `nb_gold_build` (dims + facts, full rebuild each run — data is small) + `nb_gold_mlv` (creates MLVs, idempotent `CREATE ... IF NOT EXISTS`) | Full rebuild keeps the logic simple; incremental facts are a Phase-later optimization, note it in README |
| Units | Confirm during C4 profiling and record in the data dictionary: demand/generation expected MWh, prices €/MWh | Don't assert units the API didn't state |

## Steps

### C1 `[YOU]` Learn first (~1–2 h, timeboxed)

- Delta Lake essentials: schema enforcement vs evolution, `OPTIMIZE`, **V-Order**,
      `VACUUM` (retention!) — `https://learn.microsoft.com/fabric/data-engineering/delta-optimization-and-v-order`.
- Why `.collect()` is dangerous (drill answer: pulls the whole distributed dataset
      to the driver → OOM; use `display()`/`limit()`/aggregations instead).
- Partitioning: our tables are small (a few 100k rows) — **don't partition** silver/
      gold; note the drill answer (partition only when partitions are ≥ ~1 GB;
      over-partitioning = small-file problem).
- Materialized lake views: `https://learn.microsoft.com/fabric/data-engineering/materialized-lake-views/overview-materialized-lake-view`.

### C1.5 `[CLAUDE]` 🎓 Understanding check — Delta, DQ gate & MLVs

- Claude quizzes Gonzalo (`AskUserQuestion`) on: **schema enforcement vs evolution**,
      why **`.collect()`** is dangerous (and what to use instead), when to **partition**
      (and why we don't here), the **write-then-raise** DQ-gate shape (why write results
      before raising), and **MLV vs a notebook-written aggregate** (when each wins).
      Diagram the medallion + DQ-gate flow (Bronze → Silver + quarantine → DQ gate →
      Gold) so the "gate between silver and gold" story is concrete.
- Record weak spots for the Phase G drills.

### C2 `[CLAUDE]` Python package + DQ module

- Branch `feature/dq-module`. Create `pyproject.toml` (hatchling; ruff + mypy strict
      config), `src/energy_lakehouse/` with:
  - `parsers.py` — typed parse functions per indicator: raw REE JSON → list of typed
    rows (`included[].attributes.values[]` flattening, UTC normalization from
    `Europe/Madrid` offsets).
  - `dq/checks.py` — `null_pct`, `value_range`, `freshness`, `row_count_delta`; each
    returns a typed `DQResult(check, table, status, observed, threshold, details)`.
  - `dq/gate.py` — `run_gate(stage, spark) -> None`: runs the stage's check config,
    appends all results to `ops.dq_results`, raises `DQGateError` listing failures.
  - Check config (constants, no magic numbers): demand > 0; generation ≥ 0;
    price in −500…4000 €/MWh; freshness: max date ≥ yesterday; row-count delta vs
    previous load within ±50 %; null % = 0 on key columns.
- `tests/` with pytest fixtures using real captured API JSON (one good + one
      malformed sample per indicator, committed under `tests/fixtures/`).
- `ruff check`, `mypy --strict`, `pytest` all green locally → PR → merge to
      `develop`.
- Build the wheel: `uv build` (or `python -m build`) →
      `dist/energy_lakehouse-0.1.0-py3-none-any.whl` (`dist/` stays gitignored).
      Tell you the exact path for C3.

### C3 `[YOU]` Fabric Environment with the wheel

- `ws-energy-dev` root → **+ New item** → **Environment** → `env_energy`.
- **Custom libraries → Upload** → pick the wheel from `dist\` (path from C2).
- **Publish** (takes ~5–10 min — start it and move on).
- Workspace settings → **Data Engineering/Science → Spark settings → Environment** →
      set `env_energy` as **workspace default**.
- Note for later: every wheel change = re-upload + re-publish (~10 min). Batch
      library changes; don't iterate through the environment.

### C4 `[YOU]` → `[CLAUDE]` Silver + DQ notebooks (hybrid flow)

- `[YOU]` Create empty notebook shells (attach `lh_energy`, commit):
      `silver/nb_bronze_to_silver`, `orchestration/nb_dq_gate`.
- `[CLAUDE]` Pull, write both in Git `.py` format on `feature/silver-transform`,
      PR → merge:
  - `nb_bronze_to_silver` — param `p_indicator`; read
    `Files/raw/<indicator>/*/*/*.json`; parse via `energy_lakehouse.parsers`;
    malformed → `silver.quarantine`; good rows → typed Delta merge (dedup on natural
    key) into `silver.demand_daily` / `silver.generation_daily` /
    `silver.price_hourly`; finish with `OPTIMIZE`.
  - `nb_dq_gate` — param `p_stage`; thin wrapper around
    `energy_lakehouse.dq.gate.run_gate`.
- `[YOU]` **Source control → Update all**; run `nb_bronze_to_silver` once per
      indicator (three runs). Verify under Tables → silver: 3 tables + `quarantine`;
      spot-check row counts vs a hand query on the API; **confirm units** and tell
      Claude for the data dictionary.
- `[YOU]` Run `nb_dq_gate` with `p_stage = silver` → expect green;
      `ops.dq_results` has one row per check. Screenshot.

### C5 `[YOU]` + `[CLAUDE]` The corrupted-file test (money screenshot #1)

- `[CLAUDE]` Craft a corrupt Bronze file from a real one (negative demand values +
      a truncated JSON record) → hand you the file at
      `docs/evidence/phase-c/corrupt_demanda_202401.json` *(kept in repo as the test
      fixture — reproducibility)*.
- `[YOU]` Upload it into `Files/raw/demanda_evolucion/2024/01/` (lakehouse Files →
      Upload), **overwriting** the real file.
- `[YOU]` Run `nb_bronze_to_silver` (demand) then `nb_dq_gate` (silver):
      truncated record → lands in `silver.quarantine`; negative values → DQ gate
      **fails with a readable `DQGateError`**. Screenshot the error + the
      `ops.dq_results` FAIL rows + the quarantine rows.
- `[YOU]` Restore: re-run `pl_ingest_ree` for `demanda_evolucion` 2024-01 (Phase B
      idempotency doing its job), re-run silver + gate → green. Screenshot.

### C6 `[YOU]` → `[CLAUDE]` Gold star schema (hybrid flow)

- `[YOU]` Create shells `gold/nb_gold_build`, `gold/nb_gold_mlv`, commit.
- `[CLAUDE]` Write on `feature/gold-star-schema`, PR → merge:
  - `nb_gold_build` — full rebuild: `dim_date` (2023-01-01 → 2027-12-31: date, year,
    month, month_name, quarter, day_of_week, is_weekend), `dim_technology` (distinct
    from silver + `is_renewable` flag from the API's renewable grouping),
    `dim_indicator` (name, source path, grain, unit), facts keyed to dims
    (`fact_demand_daily`, `fact_generation_daily`, `fact_price_hourly`).
  - `nb_gold_mlv` — `CREATE MATERIALIZED LAKE VIEW IF NOT EXISTS
    gold.mlv_monthly_renewables_share` (monthly renewables % from
    fact_generation_daily × dim_technology) + one more aggregate (monthly avg price).
- `[YOU]` Update all; run `nb_gold_build`, then `nb_gold_mlv`. Verify Tables → gold
      shows 6 tables + the MLVs.

### C7 `[YOU]` + `[CLAUDE]` SQL proofs (money screenshot #2)

- `[CLAUDE]` Write `sql/proofs/` (committed): `gold_row_counts.sql`,
      `gold_star_join.sql` (fact×dim join reproducing a known month),
      `mlv_renewables_share.sql`.
- `[YOU]` Open `lh_energy` → **SQL analytics endpoint** → run each proof → verify
      sane results → screenshot each with results visible.

### C8 `[CLAUDE]` Wrap-up

- README: honest MLV paragraph (when a declarative, engine-refreshed MLV beats a
      notebook-written aggregate — and when it doesn't: complex logic, custom schedules,
      preview limitations).
- `docs/data-dictionary.md` started (silver + gold tables, columns, units as
      confirmed in C4).
- Evidence into `docs/evidence/phase-c/`, normalize names, commit; tick
      done-criteria, Status ✅, session log.

### C9 `[CLAUDE]` + `[YOU]` 📣 Portfolio — engineering narrative

- `[CLAUDE]` Update `fabric-energy-lakehouse.mdx` (+ Es mirror): flesh out the
      medallion story now that it's real — the finalized architecture Mermaid (REE →
      Bronze Files → Silver Delta + quarantine → DQ gate → Gold star schema + MLVs), the
      **data-quality gate** as the headline engineering point (the corrupted-file
      screenshot from C5), and the typed-helpers-package / thin-notebooks claim. Fold in
      the Phase B ingestion assets. Keep `status: "in-progress"`.
- `[YOU]` Review the draft in the portfolio repo; commit it there when happy. This is
      the substantive technical write-up — the Phase E 📣 adds the visual layer on top.

## Gotchas & deviations

*(expected suspects: MLV preview syntax/limitations on schema-enabled lakehouses,
environment publish latency, Spark session cold starts on 64 CU)*

### C2 — REE payload shape (confirmed against live captures, 2026-07-18)

Captured one real sample per indicator (plus a 2024 **and** 2025 price sample) straight from
`apidatos.ree.es` to drive the parser tests. Five things the parsers now encode — each was a
guess before, now verified — and each reshapes Silver/Gold:

1. **The renewable flag is in the payload.** Each generation series carries
   `attributes.type` ∈ {`Renovable` (7), `No-Renovable` (8), `Generación total` (1)}. So
   `dim_technology.is_renewable` comes straight from the API — **no hardcoded mapping** to
   drift out of date.
2. **`Generación total` is a series, not a total field.** It sits among the 16 as the composite
   sum (`attributes.composite = True`). The parser excludes it by that flag (language-proof,
   unlike matching the title). Including it would double every daily total — the classic
   aggregate-row trap. Kept as a candidate DQ cross-check for later (Σtech ≈ total).
3. **Daily grain keys on the civil date, not UTC.** A daily bucket is stamped local midnight
   (`…T00:00+01:00`); UTC-converting it lands on the **previous day**. So demand/generation keep
   the local calendar date; only the sub-daily price instants normalize to UTC (where UTC is
   load-bearing for a DST-unique key).
4. **Price grain differs per series *within one file*.** In the 2025 sample, PVPC is still
   hourly (24 points/day) while `Precio mercado spot` is **15-minute (96 points/day)**. So
   `period_minutes` is derived per series from timestamp spacing (modal gap, DST-robust) — it
   cannot be inferred from the indicator, the file, or `time_trunc`.
5. **Structural vs semantic failure is the parser/gate boundary.** Records that can't produce a
   typed row (null value, missing datetime, non-numeric) are **quarantined by the parser**; rows
   that parse but look wrong (negative demand, out-of-range price) pass through and are **judged
   by the DQ gate**. This is exactly the C5 corrupted-file split (truncated record → quarantine;
   negative values → gate FAIL), designed in rather than discovered there.

### C4 — the DQ gate caught a real data property on first contact (2026-07-19)

The first `nb_dq_gate` (silver) run **failed**: `silver.generation_daily.value value_range:
8 rows outside [0.0, inf]`. Investigation (Q1 profiling query) showed the negatives are
isolated to **`Carbón`** (coal, non-renewable): 8 days over 3.5 years, min −120 MWh, avg −107,
against a 10⁴–10⁵ scale — the signature of **thermal station self-consumption** (a plant's net
daily output dipping slightly below zero on near-idle days). Legitimate REE data, not
corruption. This is the gate working as designed — it surfaced a real characteristic before it
reached Gold.

**Fix (data-driven, renewable-aware), wheel `0.1.0` → `0.2.0`:** renewables can't be
physically negative, so the rule flags *any* negative renewable value **and** any generation
below −1000 MWh (gross corruption), while tolerating small thermal negatives:
`(is_renewable AND value < 0) OR value < -1000`. Demand stays strict `> 0` (the signal C5
injects) and price stays `[-500, 4000]`. Documented in `docs/data-dictionary.md`.

**Profiling confirmations from the same runs:** demand 1295 days / generation 19,412 rows /
price 102,763 rows over 2023-01 → 2026-07; the UTC shift is visible (price min date
`2022-12-31` = `2023-01-01T00:00+01:00`); and the **grain split is exact** — spot is 60-min
until 2024-12-31 then 15-min from 2025-01-01 (54,140 quarter-hour rows), PVPC hourly
throughout. Every wheel change = version bump + re-upload + re-publish `env_energy` (~10 min),
so tuning is batched.

**Packaging note.** `ruff` is scoped to `src/`+`tests/` (`extend-exclude = ["fabric"]`) because
the serialized notebooks have mid-file imports and a runtime-injected `spark` — they are not
plain modules. `pyspark` is **not** a wheel dependency (Fabric provides it); the package imports
cleanly without it, and `dq/gate.py` is the only Spark-touching module (import is lazy /
`TYPE_CHECKING`). `INDICATORS` is duplicated for now between `nb_gen_chunks` and
`energy_lakehouse.indicators` — collapses in C4 once `env_energy` lets the notebook import the
wheel.

### C5 — the corrupted-file test caught a bug in the *reader*, not just the data (2026-07-19)

The injected corrupt file crashed `nb_bronze_to_silver` with a `JSONDecodeError` **before any
DQ mechanism ran** — the diagnostic scan showed the file arriving **split into one row per
line**. Root cause: a PySpark trap. `spark.read.option("wholetext", True).text(glob)` does
**not** apply wholetext — `text()` has its own `wholetext=False` keyword default and PySpark
writes every non-None method parameter over previously set options, silently clobbering it.
Correct form: `spark.read.text(glob, wholetext=True)`.

**Why it survived C4:** Fabric's JsonSink writes every Bronze file as a single line, so
line-mode and wholetext reads are indistinguishable — the bug was latent until the first
multi-line file existed, and the first multi-line file was C5's pretty-printed corrupt
fixture. Exactly the kind of implicit-contract dependency the corrupted-file test exists to
surface: the reader's correctness was resting on a *formatting habit of the producer*, not on
the code. Fixed in the same session; the multi-line fixture doubles as the regression proof.

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
