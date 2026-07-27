# Decision log

The load-bearing architectural decisions behind this lakehouse, with the *why* and the
alternative that was rejected. Ordered by the layer they touch, not chronologically. Where a
decision was later corrected by evidence, that is recorded rather than quietly overwritten —
the correction is part of the reasoning.

Cross-references: the build narrative in [`build-log.md`](build-log.md), data contracts in
[`data-dictionary.md`](data-dictionary.md).

---

## Platform & Git

### D1 — Two-track execution (Azure DevOps *and* GitHub)
**Decision.** Build the same P1 phases twice: **Track A** on a student tenant using Azure
DevOps as Fabric's Git provider, **Track B** on an own tenant using native GitHub integration.
**Why.** The student tenant blocks the GitHub provider, and demonstrating both providers is
portfolio-valuable in its own right — the divergence points (SPN CI/CD, provider setup) are
exactly what an employer asks about. Running it twice turns a tenant limitation into a
comparison.
**Consequence.** The two tracks must describe the same phases and the same end product, so
every provider-specific step is documented as a paired variant rather than a fork. A negative
result on one track (e.g. Track A's blocked SPN) *strengthens* the comparison rather than
being a gap.

### D2 — GitHub is canonical; Fabric syncs Azure DevOps (Track A)
**Decision.** Fabric ⇄ Azure DevOps for Git integration, but this GitHub repo is the durable
artifact, kept in sync by mirroring (`origin` = GitHub, `devops` = Azure DevOps).
**Why.** The student tenant forces Azure DevOps, but the portfolio lives on GitHub. Mirroring
both remotes keeps the reviewable history public.
**Consequence.** A discipline: after every commit, verify
`git rev-list --left-right --count origin/develop...devops/develop` is `0 0`. Fabric commits
land on `devops` → fetch → fast-forward → mirror to `origin`.

### D3 — Schema-enabled lakehouse (irreversible, chosen at creation)
**Decision.** Enable **Lakehouse schemas** on `lh_energy` at creation.
**Why.** It gives schema namespaces (`bronze`/`silver`/`gold` rather than one flat table list)
and is a **prerequisite for materialized lake views** (Phase C). It can only be set at
creation, so the cost of skipping it is a full rebuild.
**Rejected.** A flat non-schema lakehouse — simpler, but it forecloses MLVs and muddies the
medallion layering. (Note: schemas are *unrelated* to Direct Lake — a common conflation of a storage-layout
choice with a query-mode one.)

### D4 — develop-flow branching; `main` is the release gate
**Decision.** `feature/*` → `develop` (auto-mergeable); `develop` → `main` by PR only. Fabric's
dev workspace is bound to `develop`; `main` deploys to prod via `fabric-cicd`.
**Why.** `main` is the human review gate and the single source prod is built from. Keeping
authoring on `develop` and release on `main` maps cleanly onto the two Git mechanisms (D16).

---

## Ingestion

### D5 — Copy activity, not Copy job
**Decision.** Bronze ingestion uses a Copy **activity** even though Microsoft recommends Copy
**job** as the default and Copy job has native watermark-based incremental copy.
**Why.** Our unit of work is a **URL**, not a queryable table — the date window is baked into
the URL string, so there is nothing for Copy job to watermark against. We also need
ForEach + Invoke-pipeline composition. Copy job's headline feature doesn't apply.
**Rejected.** Copy job (no queryable source); Web activity (its response stays in pipeline run
state, size-limited and never persisted — Bronze must land a file).

### D6 — Watermark for *incremental*; deterministic overwrite for *idempotent* (two mechanisms)
**Decision.** Treat "what to fetch" and "what happens if you fetch it twice" as separate
problems: a watermark (`bronze.ctl_watermark`) decides the window; a deterministic path +
Copy **overwrite** makes a re-run safe.
**Why.** Conflating them is a trap. Idempotency that actually rests on the
watermark evaporates on the failed run — where the watermark never moved. The kill-test (B8c)
proved it: a cancelled backfill re-ran to an identical file set with the watermark untouched.
**Consequence.** The watermark is written **only after a successful copy**, so a failure yields
re-fetch pressure, never a silent gap.

### D7 — Serialize the watermark writes
**Decision.** Chain the three per-indicator watermark MERGEs sequentially
(`nb_wm_demanda → generacion → precios`) rather than running them in parallel off the ForEach.
**Why.** Three parallel MERGEs into one unpartitioned Delta table race to commit the next
version; one wins, the rest throw `ConcurrentAppendException`. This actually
failed in B7. A conflict needs *the same table AND a writer that also read it* — serializing
removes the race.
**Rejected.** Partition-per-indicator (over-engineering three tiny rows); blind retry (a
band-aid, not a fix).

---

## Transform & data quality

### D8 — Typed wheel package + thin notebooks
**Decision.** All parsing and DQ logic lives in a typed, `mypy --strict`, unit-tested Python
package (`energy_lakehouse`, shipped as a wheel into a Fabric Environment). Notebooks are thin
orchestration.
**Why.** DQ policy is code worth testing, not cells worth eyeballing. 26 tests over real REE
fixtures; the package is deliberately **Spark-free at import** so it tests without a cluster.
**Consequence, accepted knowingly.** A threshold change is a wheel rebuild + environment
re-publish (~10 min), not a cell edit — the price of DQ being unit-tested. This cost was paid
in the open when the coal-negatives fix shipped as wheel 0.2.0.

### D9 — Structural quarantine vs semantic gate (write-then-raise)
**Decision.** Two failure modes, two mechanisms. **Structural** problems (a null where a number
is required, a missing key) → **quarantine**, run continues. **Semantic** problems (a value
that parses fine but violates policy, e.g. negative demand) → **DQ gate**, run **fails**. The
gate writes every result to `ops.dq_results` *before* it raises.
**Why.** A row that can't become a typed row without guessing can't be judged semantically yet
— different jurisdictions. Writing all results before raising means every
failure is diagnosable from the table, not just the first in stderr.
**Evidence.** The gate caught 8 real negative-generation rows (all `Carbón`, legitimate thermal
self-consumption) and a corrupted-file test drove the full fail→clean→green arc.

### D10 — Full atomic gold rebuild; natural keys, not surrogates
**Decision.** `nb_gold_build` rebuilds the star schema from scratch each run (no MERGE), joining
on **natural keys** (`date`, `technology`) with `overwriteSchema`.
**Why.** Gold runs downstream of a green gate and is pure derivation, so a rebuild is simpler
and always consistent. Natural keys scale fine here and are friendlier to Direct Lake than
surrogate-key lookups.
**Consequence.** No surrogate `_key` columns exist — which is why the Phase E relationships join
on natural keys and `dim_indicator` is deliberately disconnected (no fact carries an indicator
column).

### D11 — Civil-Madrid date on the price fact
**Decision.** `fact_price_hourly` carries both `datetime_utc` and a Madrid **civil** `date`.
**Why.** UTC is the unique row identity across DST (a local timestamp alone is not unique twice
a year); the civil date is what a daily join *means*. `to_date(utc)` would misdate the first
1–2 h of every Madrid day onto the previous day. Neither column can replace the other — and
this is a **domain** decision, nothing to do with Direct Lake — crediting the platform for a
domain requirement is a trap worth naming.

### D12 — Materialized lake views where declarative wins
**Decision.** Two engine-refreshed MLVs for stable relational aggregates; notebook aggregates
everywhere else.
**Why.** MLVs are zero-maintenance for aggregates that are pure SQL and want engine-managed
refresh. They cost DROP+CREATE churn and a single-SELECT limit, so anything needing arbitrary
Python or custom scheduling stays a notebook. The README carries the honest version of this
trade-off.

---

## Serving

### D13 — Direct Lake **on OneLake** (not on SQL)
**Decision.** Build `sm_energy` as Direct Lake **on OneLake**.
**Why.** It reads Delta straight from OneLake (no SQL-endpoint metadata-sync lag, better DAX
plans) and — decisively — **has no DirectQuery fallback path at all**. That satisfies the
phase's "no fallback" requirement *by construction* rather than via the `DirectLakeBehavior`
toggle, which only exists for Direct Lake on SQL.
**Consequence.** The guide's "set Direct Lake behavior → Direct Lake only" step is N/A; a
rendered report *is* the no-fallback proof. Also: Direct Lake supports **no calculated
columns**, so every derived column is built in `nb_gold_build` (Spark), not the model — the
same "shape it in the lake" rule that keeps us off SQL views.

### D14 — Assume referential integrity on all relationships
**Decision.** Tick **Assume referential integrity** on the four fact→dim relationships.
**Why.** It lets the engine use INNER instead of LEFT OUTER joins. Safe here for three specific
reasons: the calendar is a superset of the data, `dim_technology` is the exact `DISTINCT` set,
and the DQ gate enforces non-null keys. Break any one and orphan rows would be silently
dropped.

### D15 — Model-layer fixes over report formatting
**Decision.** When the first rendered report showed a nonsensical 40.5% YoY and a collapsing
month-end trend, fix them in **TMDL measures**, not in report formatting.
**Why.** Both were *model* defects, not visual ones — they'd survive any amount of polish.
`Demand YoY %` had no opinion on whether its two windows were comparable; the trend counted a
partial current month. Fixed with a self-contained rolling-12-complete-months measure and a
completeness-guarded trend + a `Data Through` freshness stamp. A report that looks wrong is not
automatically a formatting problem.

---

## Orchestration & release

### D16 — Explicit master pipeline; nothing in gold refreshes itself
**Decision.** `pl_daily_refresh` chains the whole medallion from one trigger:
ingest → 3× silver → DQ gate → gold build → MLV refresh, all on `Succeeded` dependencies.
**Why.** No layer tracks the one below it live — Direct Lake reads gold's Delta directly, so
there is no "refresh semantic model" step (that would be an Import-mode reflex), but gold *does*
need explicit rebuilding. The chain makes the data dependency real.

### D17 — Terminal-skip alert funnel + a `Fail` activity
**Decision.** One failure alert routed off the **terminal** activity with `[Failed, Skipped]`,
followed by a `Fail` activity.
**Why.** The naive design (seven `On fail` arrows into one Outlook activity) can **never fire**:
dependencies from different sources are AND'd, so all seven would have to fail at once —
impossible in a short-circuiting chain. Routing off the single terminal (`Failed` OR `Skipped`,
same-source ⇒ OR) fires exactly once on any failure. And because a *succeeding* failure-handler
flips the pipeline to `Succeeded`, a `Fail` activity re-asserts the red status. Proven with a
controlled break.

### D18 — `fabric-cicd` with parameterization; interactive-auth fallback
**Decision.** Deploy dev→prod with `fabric-cicd` driven by a typed `scripts/deploy.py` and a
`fabric/parameter.yml`. Auth is a service principal when the `FABRIC_*` env vars are present,
interactive browser otherwise.
**Why.** Git integration is *authoring* (dev ⇄ `develop`); `fabric-cicd` is *release*
(`main` → prod). Prod is **never** Git-bound — by design, not limitation (on Track A dev and
prod share the tenant, so integration is available and deliberately refused): binding it would
copy dev's GUIDs verbatim, skip the gate, make prod hand-editable, and deploy as the wrong
identity. The SPN path is blocked on the student tenant (Entra admin centre
401), so prod deploys by running the same script locally with interactive auth — same code,
same commit, different identity and trigger. The workflow ships anyway, gated off.

### D19 — Parameterize only what genuinely differs (and what that taught us)
**Decision.** `parameter.yml` rewrites **notebook** lakehouse/workspace bindings only.
**Why, learned across F3–F7.** Pipelines auto-re-point same-workspace references, so they need
no entry. `$items.Lakehouse.lh_energy.$id` resolves *after* the target is created, which
**removed the two-pass bootstrap** the guide assumed. Connections aren't parameterized because
they're tenant-level — but "reused" is not "portable": **anonymous** connections travel across
a deploy, **OAuth/credentialed** ones (Outlook) must be **re-authenticated per environment**, or
Fabric rejects the pipeline at submission. And because `fabric-cicd` publishes from the
**filesystem, not git**, a gitignored `__pycache__/*.pyc` leaked in as a definition part and
broke the first deploy — so `deploy.py` now strips bytecode caches before publishing.
