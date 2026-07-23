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
| `scripts/` | `deploy.py` — the dev → prod release command |
| `fabric/` | Fabric item definitions synced as code via Git integration, plus `parameter.yml` |
| `docs/` | Architecture, decision log, capacity-cost notes, per-phase build journal |
| `.github/workflows/` | `deploy-prod.yml` — release pipeline as code |

## CI/CD — two mechanisms, pointing in opposite directions

The single most common misconception about Fabric source control is that Git integration
*is* the deployment mechanism. It isn't, and the distinction is the backbone of this
project's release model:

> **Git integration** = dev workspace ⇄ `develop`. Bidirectional, manual, interactive,
> and it is for **authoring**.
> **`fabric-cicd`** = `main` → prod workspace. One-way, scripted, gated, and it is for
> **releasing**.
>
> **The prod workspace is never bound to Git and is never hand-edited.**

Binding prod to `main` and clicking *Update all* looks equivalent and is not, for four
independent reasons — any one of which is disqualifying:

1. **No parameterization.** Git integration copies definitions verbatim. Fabric bakes
   dev-tenant GUIDs into items whether you want it to or not: every notebook pins a
   `default_lakehouse` and a `default_lakehouse_workspace_id`, and pipelines carry the
   lakehouse `artifactId` and a connection GUID. Pulled straight into prod, those still
   address **dev's** objects. `fabric/parameter.yml` is the seam that rewrites them.
2. **It isn't CI/CD.** It's a person clicking a button — no trigger, no gate, no run log.
3. **It makes prod writable.** A Git-bound workspace has a Source control panel, so prod
   can be hand-edited and committed *back* to `main`.
4. **Wrong identity.** A release should deploy as a service principal, not as whoever
   happened to be logged in.

### Running a release

```bash
uv sync --group deploy
python scripts/deploy.py --environment prod
```

The script picks its authentication path automatically: a service principal when
`FABRIC_CLIENT_ID` / `FABRIC_CLIENT_SECRET` / `FABRIC_TENANT_ID` are set, otherwise an
interactive browser login.

### The service-principal path, and why it doesn't run here

`.github/workflows/deploy-prod.yml` implements the enterprise pattern — merge to `main`
triggers a deploy as a service principal — and ships in the repo, gated behind an
`SPN_ENABLED` repository variable so it exists without firing.

It does not run on the tenant this was built on. The Microsoft Entra admin centre returns
**HTTP 401** for this account, on both the Entra blade and the App-registrations deep
link, so the student tenant has *"Restrict access to Microsoft Entra admin center"*
enabled and app registration is unreachable — not merely disabled. A knock-on worth
stating precisely: the Fabric *"Service principals can use Fabric APIs"* setting is
therefore **unverifiable** here rather than known-disabled, because reading it needs the
same admin portal.

So prod is deployed by running that same script locally with an interactive login: same
code, same `parameter.yml`, same reviewed commit — only the identity and the trigger
differ. The gap is a tenant policy, not an architectural one, and it is documented rather
than papered over.

## License

[MIT](LICENSE)
