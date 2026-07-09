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
