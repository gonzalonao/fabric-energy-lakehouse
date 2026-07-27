# Phases — what was built, and where the proof is

The lakehouse was built in seven phases, each with its own done-criteria and its own evidence
folder. This page is the **inventory**: what exists after each phase, and a link to the
screenshots that prove it.

For the *story* — the incidents, the things that broke and what each one forced — read
[`build-log.md`](build-log.md). For *why* each choice was made, read
[`decisions.md`](decisions.md).

Every evidence folder carries its own `README.md` cataloguing what each screenshot
demonstrates, so a reader can check a claim without having to interpret a raw image.

| Phase | Focus | Status | Evidence |
|---|---|---|---|
| [A](#phase-a--platform--source-control) | Platform & source control | ✅ | [6 screenshots](evidence/phase-a/) |
| [B](#phase-b--batch-ingestion) | Batch ingestion | ✅ | [19 screenshots](evidence/phase-b/) |
| [C](#phase-c--transform--data-quality) | Transform & data quality | ✅ | [11 screenshots](evidence/phase-c/) |
| [D](#phase-d--orchestration) | Orchestration | ✅ | [7 screenshots](evidence/phase-d/) |
| [E](#phase-e--serving) | Serving | 🚧 | [2 screenshots](evidence/phase-e/) |
| [F](#phase-f--cicd) | CI/CD & release | ✅ | [6 screenshots](evidence/phase-f/) |
| [G](#phase-g--evidence--documentation) | Evidence & documentation | 🚧 | *(this page and its siblings)* |

---

## Phase A — Platform & source control

Standing up the workspace and proving that Fabric items can genuinely live in Git.

**Built**

- Two workspaces (`ws-energy-dev`, `ws-energy-prod`) on trial capacity, large semantic model
  format on, template apps off.
- `lh_energy` — the lakehouse, created with **schemas enabled**. Irreversible, and a
  prerequisite for materialized lake views later.
- Workspace folder structure: `bronze` / `silver` / `gold` / `orchestration`.
- An Azure DevOps organisation, project and repository, with Fabric's Git integration binding
  the dev workspace to `develop` at `/fabric`.
- `nb_smoke_test` — a throwaway notebook used to exercise the full round trip.

**Proved**

- A commit made *from Fabric* appears on the branch, and a change made *on the branch* appears
  in Fabric after *Update all* — integration verified in both directions rather than assumed.
- Notebooks serialize as `.py`, so a pull request produces a readable one-line diff.

📁 [`evidence/phase-a/`](evidence/phase-a/)

## Phase B — Batch ingestion

Getting three REE indicators into Bronze, incrementally and safely.

**Built**

- `vl_energy` — variable library holding the alert address and the backfill start date, so
  neither is hardcoded in a pipeline.
- `pl_ingest_ree` — the core ingestion pipeline: Copy activity against the REST connection,
  retry 3 × 60 s, failure alert on the `On fail` branch.
- `nb_gen_chunks` — generates the month-sized windows the API requires, in both backfill and
  daily modes.
- `nb_update_watermark` + `bronze.ctl_watermark` — the incremental control table, written
  **only after a successful copy**.
- `pl_backfill_ree` (history load) and `pl_ingest_daily` (incremental), plus a daily schedule.

**Proved**

- Full history loaded — **129/129 files verified byte-level** against the source envelope.
- An incremental run fetches only new dates; a **cancelled run re-runs to a byte-identical file
  set**, with the watermark demonstrably untouched.
- Watermarks deliberately regressed by two weeks self-healed on the next daily run.

📁 [`evidence/phase-b/`](evidence/phase-b/) — the largest evidence set, because this is where
idempotency had to be demonstrated rather than claimed.

## Phase C — Transform & data quality

Typed Silver, a real DQ policy, and a Gold star schema.

**Built**

- `energy_lakehouse` — a typed Python package (`mypy --strict`, Ruff, **26 pytest tests** over
  real captured API responses), deliberately Spark-free at import so it tests without a
  cluster. Shipped as a wheel.
- `env_energy` — the Fabric Environment carrying that wheel, set as the workspace Spark
  default. The `.whl` serializes into Git, so the Environment is itself deployable.
- `nb_bronze_to_silver` — parse, quarantine, natural-key merge, optimize.
- `nb_dq_gate` — semantic checks that write every result to `ops.dq_results` **before**
  raising.
- `nb_gold_build` — full atomic star-schema rebuild: `dim_date`, `dim_technology`,
  `dim_indicator`, `fact_demand_daily`, `fact_generation_daily`, `fact_price_hourly`.
- `nb_gold_mlv` — two engine-refreshed materialized lake views.
- [`sql/proofs/`](../sql/proofs/) — three SQL scripts verifying the star schema from the
  lakehouse endpoint, independently of the pipeline that built it.
- [`data-dictionary.md`](data-dictionary.md) — column-level contracts for every Silver and Gold
  table.

**Proved**

- Structurally invalid rows land in quarantine and the run continues; semantically invalid rows
  fail the run with a message naming the rule, table, column and row count.
- A deliberately corrupted file drove the full **fail → fix → green** arc.
- A monthly renewables share reproduces identically three ways — star join, materialized view,
  and DAX measure.

📁 [`evidence/phase-c/`](evidence/phase-c/) — includes the corrupted fixture used for the DQ
test.

## Phase D — Orchestration

One trigger, the whole medallion, and an alert that actually fires.

**Built**

- `pl_daily_refresh` — the master pipeline: ingest → three silver notebooks (sequential) → DQ
  gate → gold rebuild → MLV refresh, all on `Succeeded` dependencies.
- `alert_on_fail` — a single failure alert routed off the **terminal** activity on
  `Failed` **or** `Skipped`, so it fires exactly once for a failure anywhere in the chain.
- `fail_run` — a `Fail` activity that re-asserts a red run status, because a failure handler
  that *succeeds* would otherwise flip the whole run to `Succeeded`.
- The daily schedule moved onto the master pipeline; the standalone ingest schedule disabled,
  so ingestion runs once per morning rather than twice.

**Proved**

- Three consecutive **unattended scheduled runs** green, with `Run kind = Scheduled` — the
  column that distinguishes a real trigger from a manual start.
- A controlled break produced exactly one alert email, gold correctly skipped, and an honest
  red status — and the email is evidenced **in the recipient's inbox**, not just as a succeeded
  activity in Monitor. A succeeded send activity proves the call was made, not that mail
  arrived.

📁 [`evidence/phase-d/`](evidence/phase-d/)

## Phase E — Serving

A curated semantic model and a report over it.

**Built**

- `sm_energy` — a custom semantic model in **Direct Lake on OneLake** mode (not the auto-generated
  default), with four natural-key relationships, `dim_date` marked as the date table, and
  **11 DAX measures**.
- `rpt_energy` — a three-page report: Demand, Generation mix, Prices.

**Proved**

- All pages render. Because Direct Lake on OneLake has **no DirectQuery fallback path at all**,
  a rendered report *is* the no-fallback proof — there is no silent downgrade available.
- Measures cross-check against the Phase C SQL proofs to the decimal.

🚧 **Still open:** a report formatting pass in Power BI Desktop (the web editor is too slow for
polish), after which the report screenshots will be refreshed. The model itself is complete.

📁 [`evidence/phase-e/`](evidence/phase-e/)

## Phase F — CI/CD

A release path that is code, and a production environment nobody touches by hand.

**Built**

- [`scripts/deploy.py`](../scripts/deploy.py) — the dev → prod release command, selecting a
  service principal or an interactive login automatically.
- [`fabric/parameter.yml`](../fabric/parameter.yml) — per-environment rewriting of the bindings
  Fabric bakes into item definitions.
- [`.github/workflows/deploy-prod.yml`](../.github/workflows/deploy-prod.yml) — the
  merge-to-`main` release workflow, gated behind a repository variable.
- A production workspace built **exclusively** by that script, plus branch protection making
  `main` reachable only through a pull request.
- Release **`v1.0.0`**.

**Proved**

- All 16 item definitions deploy from a reviewed commit into a workspace that has never been
  hand-edited.
- Production loaded its own history by running its own deployed pipelines — the environments
  share definitions, never storage.
- **Production is self-operating**: the daily schedule deployed as part of the item definitions
  and fired unattended the next morning.
- Two defects were caught by running the release rather than reviewing it, and both are
  documented in [`build-log.md`](build-log.md) rather than quietly patched.

📁 [`evidence/phase-f/`](evidence/phase-f/)

## Phase G — Evidence & documentation

Making the work legible to someone who wasn't there.

**Built**

- [`README.md`](../README.md) — the entry point.
- [`decisions.md`](decisions.md) — 19 decisions, each with its rejected alternative and, where
  one was later corrected by evidence, the correction recorded rather than overwritten.
- [`capacity-notes.md`](capacity-notes.md) — how Fabric actually charges compute, measured run
  costs, and an honest SKU-sizing argument.
- [`build-log.md`](build-log.md) — the build narrative.
- `phases.md` — this page.
- Per-phase evidence catalogs explaining what each screenshot demonstrates.

🚧 **Still open:** a short demo recording, and a final pass over the evidence pack.

---

## A note on scope

Two things deliberately sit outside these phases:

- **A second Git provider.** The same phases are designed to be repeated on native GitHub
  integration with a working service-principal CI/CD path, on a tenant without the restrictions
  this build hit. The blocked path is documented on this track rather than omitted.
- **Streaming.** A Real-Time Intelligence extension — Eventstream → Eventhouse/KQL → Activator
  — is planned as a counterpart to this batch platform.
