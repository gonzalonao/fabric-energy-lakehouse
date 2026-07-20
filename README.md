# fabric-energy-lakehouse

Production-shaped batch lakehouse on **Microsoft Fabric** over the Spanish electricity
market (REE open data, `apidatos.ree.es`).

**Status: 🚧 in development** — the architecture below is the plan; this README grows
with the build.

## Planned architecture

- **Ingestion** — Fabric Data Factory pipeline, parameterized with incremental
  watermarks: daily demand, generation mix by technology, market prices (2023 → now
  backfill, then daily runs).
- **Medallion lakehouse** — Bronze raw JSON → Silver typed Delta tables (PySpark) →
  Gold star schema, with data-quality gates that fail the run on breach.

### Materialized lake views — where they earn their keep, and where they don't

Gold carries two **materialized lake views** (`mlv_monthly_renewables_share`,
`mlv_monthly_avg_price`) alongside the notebook-built star schema, deliberately using both
mechanisms side by side. An MLV wins when the aggregate is **stable, relational, and
maintenance-free by design**: one `CREATE MATERIALIZED LAKE VIEW` statement, and the engine
owns refresh, lineage and storage — no notebook, no schedule of ours, no orchestration edge.
It is the wrong tool when the logic outgrows a single SQL `SELECT` (the star build needs
Python — a generated calendar, wheel-imported indicator metadata), when refresh must be
sequenced inside a pipeline's DQ-gated flow rather than on the engine's cadence, or when the
definition churns — changing an MLV means `DROP` + re-`CREATE`, not an idempotent edit. Rule
of thumb applied here: **facts and dims are built imperatively (testable, gate-sequenced);
last-mile aggregates that a BI page reads are declared as MLVs.** They require a
schema-enabled lakehouse — chosen (irreversibly) at creation for exactly this payoff.
- **Serving** — custom Direct Lake semantic model + Power BI report.
- **Streaming extension** (`streaming/`) — Eventstream → Eventhouse/KQL → Activator
  alerting (Real-Time Intelligence).
- **CI/CD** — Fabric Git integration (dev workspace ↔ `develop`); `main` deploys to the
  prod workspace with `fabric-cicd` in GitHub Actions.

## Repo layout

| Path | Contents |
|---|---|
| `src/` | Typed Python helper modules (data-quality checks, ingestion utils) |
| `docs/` | Architecture, decision log, capacity-cost notes |
| *(Fabric items)* | Notebooks, pipelines and semantic models synced as code via Git integration |

## License

[MIT](LICENSE)
