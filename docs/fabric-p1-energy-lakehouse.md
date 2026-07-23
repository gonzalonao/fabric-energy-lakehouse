# P1 — `fabric-energy-lakehouse` (flagship, D1–D7)

Last updated: 2026-07-10 · Part of [[fabric-portfolio-plan]]

**Goal:** a production-shaped, DP-700-shaped batch lakehouse on Fabric over the Spanish
electricity market (`apidatos.ree.es`, tokenless): Data Factory ingestion with incremental
watermarks → medallion Lakehouse (PySpark, Spark 4.0 / Runtime 2.0) → data-quality gates →
Gold star schema (+ materialized lake views) → Direct Lake Power BI → Git-integrated
dev/prod with `fabric-cicd` CI/CD. This is the anchor project; everything later reuses its
workspace, data, and CI/CD skeleton.

**Minimum shippable (cut line):** phases A–E on a single workspace with manual promotion;
CI/CD (F) degrades to a documented local `fabric-cicd` run.

## Phase A — Platform & Git (D1)

- Workspaces `ws-energy-dev` and `ws-energy-prod` on the trial capacity.
- Bind `ws-energy-dev` ↔ GitHub `fabric-energy-lakehouse` branch `develop` (Git
  integration). Verify a notebook round-trips as `.py` and shows diffs in PRs.
- Repo skeleton: `README.md`, `CLAUDE.md` (develop-flow), `docs/`, `.gitignore`, `src/`
  for non-Fabric helper code.
- **Done:** commit from Fabric appears on `develop`; workspace folder structure
  (`bronze/silver/gold/orchestration`) in place.

## Phase B — Batch ingestion (D2–D3)

- Learn first: pipeline anatomy (activities, parameters, triggers), Copy activity vs Web
  activity, Variable Libraries (new — runtime-resolved env config).
- Indicators from `apidatos.ree.es` (JSON, no token): daily demand evolution
  (`demanda/evolucion`), generation mix by technology (`generacion/estructura-generacion`),
  real-time market prices (`mercados/precios-mercados-tiempo-real`). Stretch: PVPC via
  ESIOS token (received 2026-07-10 — REE conditions and design rules: [[esios-api-usage]]).
- Build pipeline `pl_ingest_ree`: parameterized (indicator, date range) → Web/Copy →
  Bronze **Files** as raw JSON partitioned `indicator/year/month/`; watermark table in the
  lakehouse + Lookup activity for incremental daily runs; ForEach-driven backfill
  (2023-01 → now); retry policy + on-failure Teams/Outlook activity; daily schedule.
- **Done:** backfill loaded; daily incremental run picks up only new dates (prove it in
  run history screenshots); a killed run re-runs idempotently.

## Phase C — Transform & data quality (D3–D5)

- Learn first: Delta Lake essentials (schema enforcement/evolution, `OPTIMIZE`, V-Order,
  `VACUUM`), why `.collect()` is dangerous, partitioning strategy.
- Bronze→Silver notebook(s): parse JSON → typed Delta tables, dedup by natural key,
  UTC-normalize timestamps, quarantine malformed rows.
- **DQ module** (`src/dq/`): typed Python checks (null %, value ranges, freshness,
  row-count deltas) writing to a `dq_results` Delta table and **raising** to fail the
  pipeline on breach — the "data quality gate" bullet recruiters ask about.
- Silver→Gold star schema: `dim_date`, `dim_technology`, `dim_indicator`,
  `fact_demand_daily`, `fact_generation_daily`, `fact_price_hourly`.
- **Materialized lake views** (new feature) for Gold aggregates (e.g. monthly renewables
  share) — one honest paragraph in README on when MLVs beat a notebook-written table.
- **Done:** a deliberately corrupted Bronze file fails the run with a clear DQ error;
  Gold tables query correctly from the SQL analytics endpoint (`.sql` proofs in repo).

## Phase D — Orchestration (D5)

- Master pipeline `pl_daily_refresh`: ingest → DQ gate → silver → gold → (later: semantic
  model refresh activity), with params flowing end-to-end; daily trigger; failure alert.
- **Done:** one-click/scheduled end-to-end run, green in run history two days straight.

## Phase E — Serving (D6)

- Custom **Direct Lake** semantic model over Gold (not the default model): relationships,
  DAX measures (peak demand, YoY demand, renewables %, rolling-30d price).
- Power BI report — this is the showcase surface, apply [[star-schema-patterns]] and the
  wiki's report craft: national demand trends, generation-mix evolution, price panel.
- **Done:** report renders in Direct Lake mode (verify no fallback to DirectQuery);
  screenshots + measure definitions (TMDL) in repo.

## Phase F — CI/CD (D6–D7)

- `fabric-cicd` (Python lib) deploying `main` → `ws-energy-prod` in GitHub Actions;
  Variable Library / parameterization for dev-vs-prod values; PR gate on `develop`→`main`
  per develop-flow. SPN auth if the tenant allows an app registration; else run the same
  script locally with user auth and document the SPN pattern.
- **Done:** merge to `main` (or documented local run) reproduces the solution in the prod
  workspace untouched by hand.

## Phase G — Evidence & docs (D7)

- README (architecture Mermaid, data dictionary, run instructions), `docs/decisions.md`,
  Capacity Metrics screenshots + CU-cost notes per workload, 60–90 s demo recording.
- Wiki note: create [[fabric-lakehouse]] (gotchas, patterns, drill answers). Update
  [[azure-fabric]] with corrections.

## Interview drills (no notes, out loud)

Direct Lake vs Import vs DirectQuery (and fallback behavior); Lakehouse vs Warehouse
decision; medallion rationale per layer; incremental watermark design; idempotent re-runs;
Delta OPTIMIZE/V-Order/VACUUM; materialized lake views vs notebook tables; CU smoothing &
throttling basics; how Git integration + fabric-cicd map to enterprise release flow;
Fabric Data Factory vs ADF differences.
