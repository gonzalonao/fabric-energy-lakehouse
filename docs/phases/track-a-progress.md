# Track A — progress (Azure DevOps · student tenant)

**This file is the single progress record for Track A.** Instructions live in the phase
guides (`phase-*.md`); steps marked `[Track B]` there don't apply here. Sibling tracker:
[track-b-progress.md](track-b-progress.md) · definitions: [tracks.md](tracks.md).

**Tenant/capacity:** ESESA/UCAM student tenant · Fabric trial capacity ·
window ends ~2026-07-31.
**Git:** Fabric ↔ Azure DevOps repo (`develop`, `/fabric`); GitHub canonical via mirror.
**Status:** 🚧 **Phase C — Transform & DQ in progress** (C1, C1.5 🎓 6/6, C2, C3, **C4 done**
— silver loaded, DQ fix 0.2.0 published, gate green 20/20 PASS, evidence captured).
Next: **C5** — corrupted-file test (fail → clean → green).
Phase B ✅ complete (2026-07-17); fully closed 2026-07-19 (`b9-scheduled-run-green.png`).
Phase A ✅ complete (2026-07-14).
**DevOps:** org `glopezc443` · project/repo `fabric-energy-lakehouse` · remote `devops`
(`https://dev.azure.com/glopezc443/fabric-energy-lakehouse/_git/fabric-energy-lakehouse`).
**Dev workspace GUID:** `476b58fd-19e3-4c0d-bde7-c3f16d2a6fcf`.

## Item & connection IDs (dev) — Phase F `parameter.yml` input

Collected as they appear (per the phase-B guide: gather them now, not archaeologically at F2).
**Every value below is dev-specific and must be substituted for prod**, and all of them change
again on Track B's tenant.

| Item | ID as written in definitions | Referenced by |
|---|---|---|
| `lh_energy` (lakehouse) | `8bdb6c16-94fa-9379-43ad-836e6cabfc1b` | **pipelines** (`artifactId`) |
| `lh_energy` — **reversed encoding** | `6cabfc1b-836e-43ad-9379-94fa8bdb6c16` | **notebooks** (`default_lakehouse`, `known_lakehouses[].id`) |
| `pl_ingest_ree` | `4f47585b-30ce-947e-4fac-7d2ea13339dd` | `pl_backfill_ree` (`pipelineId`) |
| `nb_gen_chunks` | `7ec6dc40-6091-aa9e-4141-ce923e668746` | `pl_backfill_ree`, `pl_ingest_daily` (`notebookId`) |
| ~~`nb_gen_backfill_chunks`~~ | ~~`571188e6-34df-b411-40cd-66dbf619b3a1`~~ | **retired 2026-07-16** — superseded by `nb_gen_chunks` |
| `nb_update_watermark` | `e3aee25b-ed44-a622-491c-14d6c55fa8b3` | `pl_backfill_ree` ×3 (`notebookId`) |
| `conn_ree_apidatos` (REST) | `3cc793f5-7a71-4133-8102-f88cadcd4458` | `pl_ingest_ree` (`externalReferences.connection`) |
| `conn_fabric_pipelines` | `7409c7aa-34fa-4e2a-98a6-f983c750e3f3` | `pl_backfill_ree` → `inv_ingest` |
| `env_energy` (Environment) | `3b5f385e-8165-b78f-4b3a-72bf5981e359` (`logicalId`) | workspace Spark default; notebooks (C4+) |

**Three things this table is trying to stop:**

1. **The lakehouse has two encodings.** Substituting only the pipeline form leaves every notebook
   writing into **dev** while the pipelines correctly target prod — a half-migrated deploy that
   doesn't error. See the guide's Gotchas 2026-07-16.
2. **Connections don't deploy.** Both `conn_*` entries live in the **tenant**, not in Git; the
   definitions carry only GUIDs. Prod needs its **own** connections created first, and
   `conn_fabric_pipelines` currently holds *Gonzalo's user token* — correct in dev, wrong in
   prod (needs SPN or workspace identity).
3. **`workspaceId` is `00000000-…`** everywhere — a same-workspace placeholder, so workspace IDs
   need **no** substitution. Only item and connection GUIDs do.

*(Item IDs = the item's `logicalId` from its `.platform`. Verified for `lh_energy` and
`nb_update_watermark`.)*

## Phase A — Platform & Git · [guide](phase-a-platform-git.md) · ✅

- [x] A1 — two workspaces on trial capacity *(confirmed 2026-07-13 — Large semantic
      model format, template apps off)*
- [x] A2 — folders `bronze/silver/gold/orchestration` *(confirmed 2026-07-13)*
- [x] A3 — lakehouse `lh_energy`, **schemas enabled** *(confirmed 2026-07-13 — schemas
      checkbox ticked; irreversible setting verified)*
- [x] A4 — `[Track A]` DevOps org + project + repo import *(org `glopezc443`,
      project/repo `fabric-energy-lakehouse`, `develop` default; imported from GitHub)*
- [x] A5 — bind `ws-energy-dev` ↔ `develop` (`/fabric`) *(connected; first sync
      committed `lh_energy` to DevOps)*
- [x] A6 — verify sync landed; add `devops` remote; mirror to GitHub *(Fabric commit
      `ca6ccdd` mirrored to `origin`; origin/devops in sync)*
- [x] A7 — smoke-test notebook committed from Fabric *(commit `826232f`; runs
      `smoke=1`; landed at `fabric/orchestration/nb_smoke_test.Notebook/`)*
- [x] A8 — `.py` round-trip PR on GitHub; push merge to `devops` *(PR #1, clean 1-line
      diff `SELECT 1`→`SELECT 2` + comment; squash-merged `92cf0e3`; mirrored to devops)*
- [x] A9 — Update all in Fabric; edit visible *(2026-07-13 — Update all pulled PR #1;
      notebook shows `SELECT 2` + comment)*
- [x] A10 — evidence captured + committed *(6 screenshots in
      [`docs/evidence/phase-a/`](../evidence/phase-a/); Entra email redacted from `a5` —
      public repo. A7 mid-commit panel not captured; commit `826232f` evidences it)*
- [x] A11 — 🎓 Git-integration understanding check *(3/4 — see Learning log below)*
- [x] A12 — 📣 portfolio entry seeded *(EN + ES drafts written, site build passes;
      held on branch `feat/fabric-energy-lakehouse-entry` in the portfolio repo — merge to
      `main` at the Phase G 📣 checkpoint, see session log)*

Done criteria:
- [x] Commit made from Fabric visible on `develop` *(`ca6ccdd` lakehouse, `826232f`
      notebook — mirrored to GitHub)*
- [x] Workspace folder structure in place *(`a2-folders-lakehouse.png`)*
- [x] Notebook round-trips as `.py` with readable PR diff *(PR #1 — `a8-pr-diff.png`;
      pulled back into Fabric — `a9-notebook-select2.png`)*

## Phase B — Batch ingestion · [guide](phase-b-batch-ingestion.md) · ⬜

- [x] B1 — learn first (pipelines, Copy vs Web, variable libraries) *(MS Learn ToC had been
      reorganized — corrected page links recorded in the guide; API probed live)*
- [x] B1.5 — 🎓 ingestion & watermark check *(4/6 — M4, M5 opened; see Learning log)*
- [x] B2 — variable library `vl_energy` *(Fabric commit `2c68ccc`; `v_alert_email` +
      `v_backfill_start`, both String; mirrored to `origin`. Pending-commit panel captured —
      the shot missed at A7)*
- [x] B3 — core pipeline `pl_ingest_ree` (+ unit idempotency proof) *(commit `021b0a4`;
      definition reviewed — no secrets, alert email is a library-variable reference; but two
      dev GUIDs baked in → Phase F `parameter.yml` requirement, see guide Gotchas)*
- [x] B4 — watermark + chunking notebooks (hybrid flow) *(shells `6e496d2`; code via
      [PR #2](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/2) → `3fac95a`;
      pulled via Update all; `bronze.ctl_watermark` bootstrapped — **`bronze` confirmed a real
      schema node**, validating A3/M2)*
- [x] B5 — backfill pipeline `pl_backfill_ree` *(commit `d81de3d`; new **Invoke pipeline**
      activity + `conn_fabric_pipelines` — see guide Gotchas. Review caught `nb_chunks`'s base
      parameters serialized as empty literals → fix commit pending)*
- [x] B6 — daily pipeline `pl_ingest_daily` *(`5af9018`; **redesigned** — Lookup on the SQL
      endpoint proved unusable, replaced by `nb_gen_chunks` in `daily` mode
      ([PR #3](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/3), `25a5f9a`).
      `nb_gen_backfill_chunks` retired `48be9de`. Both pipelines reviewed — structurally
      identical, all checks pass)*
- [x] B7 — backfill run 2023-01 → now *(data complete: **129/129 files verified** byte-level
      (JSON:API envelope, correct windows; Fabric's JsonSink adds a UTF-8 BOM — Phase C reader
      note). The run itself finished **Failed**: the three parallel watermark MERGEs collided →
      `ConcurrentAppendException` (guide Gotchas, **M6**). Watermark repaired manually via
      `nb_update_watermark`; both pipelines rewired to a sequential watermark chain, committed
      from Fabric as `0510dc2`. M4's design proved itself: failure produced re-fetch pressure,
      never a gap)*
- [x] B8 — incremental + idempotent + kill-test proofs *(all four sub-proofs green in one
      evening: **B8a** no-op run = first end-to-end proof of the serialized watermark chain
      (Gantt: strictly sequential `nb_wm_*`); **B8b** simulated 3-day lag → 1 month-to-date
      chunk, month file overwritten whole — **3m42s/5m16s daily vs 3h53m49s backfill**;
      **B8c** kill-test: Cancelled at 2m46s → same-params re-run green 7m22s, file set
      identical; **B8d** watermarks regressed to `06-30` by design, one daily run self-healed
      them to `07-16` — **M4 demonstrated live**. 8 screenshots in evidence/)*
- [x] B9 — daily schedule active *(daily 08:00 Madrid, start 07-18, last run 07-30; the
      schedule **serializes into Git** as a dedicated `.schedules` file (`f233aef`) — own
      JSON schema, `localTimeZoneId: Romance Standard Time` — so it deploys with the
      definition in Phase F. First unattended run verified tomorrow: screenshot pending,
      reminder scheduled)*
- [x] B10 — review + evidence + 📣 asset capture *(definition review passed: no secrets or
      hardcoded emails (alert via library variable), Copy retry 3×60s, both ForEach
      Sequential, watermark chains serialized, raw passthrough confirmed (no translator),
      sink `workspaceId` all-zeros = current-workspace binding. Non-blocking: default 12h
      activity timeouts; notebooks retry 0 — acceptable, daily self-heals. Evidence: 12
      screenshots cataloged in `docs/evidence/phase-b/`)*

Done criteria:
- [x] Backfill loaded for all three indicators *(129/129 files verified; 3h53m49s)*
- [x] Incremental run fetches only new dates (screenshots)
- [x] Killed run re-runs idempotently
- [x] Schedule + failure alert wired *(alert wired in B3; schedule committed `f233aef`)*

## Phase C — Transform & DQ · [guide](phase-c-transform-dq.md) · ⬜

- [x] C1 — learn first (Delta, V-Order, partitioning, MLVs) *(taught in-session in depth —
      Delta log anatomy, enforcement vs evolution, V-Order/OPTIMIZE/VACUUM manual-vs-auto split,
      `.collect()` OOM, ~1 GB partition rule, MLV vs notebook aggregate; medallion+DQ-gate
      diagram drawn)*
- [x] C1.5 — 🎓 Delta/DQ/MLV check *(**6/6 — first perfect check**; see Learning log)*
- [x] C2 — `energy_lakehouse` package + DQ module + tests + wheel *(hatchling package in
      `src/`; typed parsers + pure DQ checks + write-then-raise gate; 24 tests over **real
      captured REE fixtures**; ruff + `mypy --strict` + pytest all green;
      [PR #4](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/4) → `2c2ea00`.
      Wheel: `dist/energy_lakehouse-0.1.0-py3-none-any.whl` (gitignored) for C3)*
- [x] C3 — Fabric environment `env_energy` with the wheel *(created, wheel uploaded as custom
      library, published, set as workspace Spark default. **Fabric serialized the `.whl` binary
      into Git** under `fabric/env_energy.Environment/Libraries/CustomLibraries/` (14 KB) —
      so the Environment is reproducible/deployable by fabric-cicd in Phase F. Commit `f08e448`,
      mirrored to origin (0/0). No `.gitignore` conflict — `*.whl` is not globally ignored, only
      `dist/`)*
- [x] C4 — silver + DQ-gate notebooks; units confirmed *(both notebooks **written**:
      `nb_bronze_to_silver` (p_indicator; glob→parse→quarantine + natural-key MERGE→OPTIMIZE)
      and `nb_dq_gate` (p_stage; thin wrapper on `run_gate`) —
      [PR #5](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/5). Field order/types
      verified vs Silver schemas locally; both compile. **Remaining `[YOU]`: Update all → run
      `nb_bronze_to_silver` ×3 indicators → verify tables + confirm units → run `nb_dq_gate`
      (silver) green.** Mirror note: squash-merge diverged origin/devops; reconciled with a
      merge commit (no force-push), both remotes 0/0. Silver loaded ✅ (3 tables, units
      confirmed → `docs/data-dictionary.md`). **DQ finding (2026-07-19):** first gate run
      flagged 8 negative generation rows — all `Carbón` (thermal self-consumption, real REE
      data). Fixed with a renewable-aware bound, wheel **0.2.0** (`48b0ff3`). **Closed
      2026-07-19:** 0.2.0 re-published to `env_energy` (Fabric commit `59441b2` — wheel binary
      renamed in Git), `nb_dq_gate` green — `ops.dq_results` latest run **20/20 PASS** —
      `c4-dq-gate-green.png` captured)*
- [ ] C5 — corrupted-file test (fail → clean → green)
- [ ] C6 — gold star schema + MLVs
- [ ] C7 — SQL proofs from the endpoint
- [ ] C8 — wrap-up (README MLV paragraph, data dictionary, evidence)
- [ ] C9 — 📣 engineering narrative in portfolio entry

Done criteria:
- [ ] Silver tables typed/deduped/UTC; quarantine works
- [ ] Corrupted Bronze file fails the run with clear DQ error
- [ ] Gold star schema built (3 dims + 3 facts)
- [ ] ≥1 MLV + honest README paragraph
- [ ] Gold queries from SQL endpoint (`.sql` proofs)

## Phase D — Orchestration · [guide](phase-d-orchestration.md) · ⬜

- [ ] D1 — master pipeline `pl_daily_refresh`
- [ ] D2 — schedule moved to master
- [ ] D3 — two-day green proof (scheduled runs)
- [ ] D4 — review + evidence + 🎓 check

Done criteria:
- [ ] End-to-end run from one trigger
- [ ] Old schedule disabled, master scheduled
- [ ] Two consecutive scheduled greens
- [ ] Single failure alert from master

## Phase E — Serving · [guide](phase-e-serving.md) · ⬜

- [ ] E1 — learn first (Direct Lake vs Import vs DirectQuery)
- [ ] E1.5 — 🎓 Direct Lake drill check
- [ ] E2 — custom semantic model `sm_energy`
- [ ] E3 — relationships, date table, Direct Lake only
- [ ] E4 — DAX measures, sanity-checked
- [ ] E5 — 3-page report `rpt_energy`
- [ ] E6 — Direct Lake verification (no fallback)
- [ ] E7 — sync + TMDL review
- [ ] E8 — 📣 visual showcase in portfolio entry

Done criteria:
- [ ] Custom Direct Lake model (not default)
- [ ] Report renders with no DirectQuery fallback
- [ ] TMDL measures in repo

## Phase F — CI/CD · [guide](phase-f-cicd.md) · ⬜

*Track A expectation: SPN blocked → documented local `fabric-cicd` fallback.*

- [ ] F1 — SPN attempt (timeboxed; outcome recorded)
- [ ] F2 — IDs collected + prod value set
- [ ] F3 — deploy code (`scripts/deploy.py`, `parameter.yml`, workflow)
- [ ] F4 — branch protection on `main`
- [ ] F5 — gated promotion PR `develop` → `main`
- [ ] F6 — deploy to prod (+ two-pass bootstrap)
- [ ] F7 — prod verified untouched-by-hand
- [ ] F8 — wrap-up + tag `v1.0.0` + 🎓 check

Done criteria:
- [ ] `develop` → `main` PR-gated
- [ ] Merge (or documented fallback) reproduces prod
- [ ] Dev/prod values via parameterization
- [ ] SPN pattern documented regardless of outcome

## Phase G — Evidence & docs · [guide](phase-g-evidence-docs.md) · ⬜

- [ ] G1 — README overhaul
- [ ] G2 — consolidated decision log
- [ ] G3 — capacity metrics + cost notes
- [ ] G4 — demo recording
- [ ] G5 — wiki notes
- [ ] G6 — interview drills out loud
- [ ] G7 — final evidence-pack gate
- [ ] G8 — 📣 portfolio finalize + CV + wiki

Done criteria:
- [ ] Recruiter-ready README
- [ ] `docs/decisions.md`
- [ ] Capacity notes + screenshots
- [ ] Demo recording linked
- [ ] Wiki notes created/corrected
- [ ] Drills done, gaps noted

## Learning (🎓)

Scores, misconceptions and the drill bank live in **[`docs/learning-log.md`](../learning-log.md)**
(cross-phase, cross-track — it also serves Track B and P2). Track A so far:

| Date | Check | Score |
|---|---|---|
| 2026-07-13 | Phase A opener (pre-build) | 1/3 |
| 2026-07-14 | A11 — Git integration (post-build) | 3/4 — 2 gaps closed, 1 open (**M3**: prod deploy direction; re-test at Phase F) |
| 2026-07-14 | B1.5 — ingestion & watermarks (pre-build) | 4/6 — 2 gaps open (**M4**: watermark ≠ idempotency, re-test at B8; **M5**: SQL endpoint is read-only, re-test at Phase C) |
| 2026-07-18 | C1.5 — Delta, DQ gate & MLVs (pre-build) | **6/6** — first perfect check; beat the "automatic" trap twice. M5 (SQL endpoint read-only) re-test still due at C7; M6 (Delta concurrency) at C4/C5 |

## Session log (Track A)

- 2026-07-10 — Repo prep before D1: standing objectives in CLAUDE.md, 📣/🎓 checkpoints
  in phase guides, C–G guides added. Phase A opened. *(shared prep, pre-tracks)*
- 2026-07-13 — A1–A3 worked through on the student tenant (workspaces on Large semantic
  model format, template apps off — pending confirmation); A5 blocked at the GitHub
  provider (see phase-a Gotchas). Tenant/trial research done; IT email drafted.
- 2026-07-13 (later) — Two-track decision (see `tracks.md`); phase-a steps rewritten as
  track variants. Progress bookkeeping moved to per-track tracker files. Next: A4
  `[Track A]` — create the Azure DevOps org.
- 2026-07-13 (resume) — A1–A3 confirmed done (lakehouse schemas verified ticked). IT
  email still not sent (Track A proceeds on Azure DevOps regardless). Starting A4.
- 2026-07-13 (resume, cont.) — A4–A6 done. DevOps org `glopezc443` created, project
  `fabric-energy-lakehouse` imported from GitHub (`develop` default). `ws-energy-dev`
  bound to DevOps `develop` at `/fabric`; first Fabric sync committed the `lh_energy`
  lakehouse. Added `devops` remote, fast-forwarded local/`origin` develop to Fabric's
  commit `ca6ccdd`, verified origin ⇄ devops in sync (0 0). Fabric committed:
  `fabric/Readme.md` + `fabric/lh_energy.Lakehouse/` (`.platform`, `alm.settings.json`,
  `lakehouse.metadata.json` = `{"defaultSchema":"dbo"}` confirming schema mode,
  `shortcuts.metadata.json`) — definitions only, no data. Next: A7 (smoke-test notebook).
- 2026-07-13 (resume, cont.) — A7–A8 done. Fabric committed `nb_smoke_test` (`826232f`)
  under `fabric/orchestration/`; `notebook-content.py` is clean reviewable Python with
  `# CELL` markers and default-lakehouse metadata. Mirrored to GitHub, branched
  `feature/git-roundtrip-check`, edited the cell (`SELECT 1`→`SELECT 2` + comment),
  opened [PR #1](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/1) (clean
  1-line diff — portfolio evidence), squash-merged (`92cf0e3`), pruned the branch, and
  mirrored `develop` to `devops`. All three (local/origin/devops) at `92cf0e3`. Next: A9
  — `[YOU]` Update all in Fabric to pull the edit back.
- 2026-07-14 — A9–A10 done. *Update all* pulled PR #1 into the workspace; `nb_smoke_test`
  shows `SELECT 2` + the round-trip comment → **bidirectional Git integration proven**.
  Evidence pack captured (6 screenshots, `docs/evidence/phase-a/`). Deviation: the A7
  mid-commit Source control panel wasn't captured (state already committed) — the commit
  is evidenced by `826232f` and the Synced status in `a2`. The Entra account email was
  **redacted** from `a5-git-integration.png` before committing (public repo, no
  evidential value). **All three Phase A done-criteria met.** Next: A11 (🎓 quiz), A12
  (📣 portfolio seed).
- 2026-07-14 — A11–A12 done → **Phase A complete.** 🎓 quiz scored 3/4: both gaps from the
  pre-build quiz are now closed; one new gap on prod-deploy direction (Learning log above).
  📣 Portfolio entry drafted in EN + ES (`fabric-energy-lakehouse.mdx` in `projects/` and
  `projectsEs/` at `../../portfolio/astro`); `npm run build` passes (27 pages, both routes
  render). **Left uncommitted on purpose** — the portfolio repo is mid-work on an unrelated
  branch (`fix/site-url-vercel`, 4 commits ahead of `main`), so committing there would
  tangle unrelated work; and A12's `[YOU]` step is Gonzalo's review call (publish as WIP now
  vs hold unlisted until Phase G). Seeded conservatively: `featured: false`, `order: 6`,
  `status: in-progress` — promote at the Phase G 📣 checkpoint.
- 2026-07-14 (later) — **A12 resolved: hold until Phase G.** The `projects` collection has no
  `draft` flag (only `writing` does), so anything on `main` renders. The drafts are therefore
  committed on branch `feat/fabric-energy-lakehouse-entry` off `main` in the portfolio repo
  (`07164fa`, pushed) and left unmerged — git-backed but off the live site, with no changes to
  the site's rendering code. **Merge that branch at the Phase G 📣 checkpoint.** Portfolio repo
  restored to `fix/site-url-vercel`. **Phase B started (B1).**
- 2026-07-14 — B1–B1.5 done. Probed all three REE endpoints live before building: all answer
  anonymously with a 1-month window (findings + the two consequences in the phase-b guide's
  Gotchas). **ESIOS stretch dropped** — `precios-mercados-tiempo-real` already returns PVPC
  tokenless, so no ESIOS token is needed anywhere in P1. Deviation: the MS Learn Data Factory
  ToC has been reorganized and the concept pages I first pointed at didn't match it — corrected
  reading list is in this session's notes (pipeline-overview, activity-overview,
  copy-data-activity, web-activity, parameters, expression-language, foreach-activity).
  Also covered **Copy job vs Copy activity** (MS now recommends Copy job as the Bronze default;
  we use Copy activity because our unit of work is a URL, not a queryable table, and we need
  ForEach + Invoke-pipeline composition — added to the drill bank). 🎓 4/6 — two new gaps
  (M4, M5) logged with corrections.
- 2026-07-14 — B2 done. `vl_energy` created at the workspace root (config is workspace-scoped,
  not an `orchestration` item) with `v_alert_email` = `gonzalonao@gmail.com` and
  `v_backfill_start` = `2023-01-01`, both **String** (no date type exists; the value is
  concatenated into a URL as text anyway). Fabric commit `2c68ccc`, mirrored to `origin`.
  Serialization confirmed before B3 references it — three files: `.platform` (carries the
  item's `logicalId`, which is what `fabric-cicd` keys on in Phase F), `variables.json`
  (the default values, in the clear — hence the PII decision in the guide's Gotchas), and
  `settings.json` with `"valueSetsOrder": []` — **the empty slot Phase F fills**: alternative
  value sets land as separate files, so the repo currently states truthfully that only one
  environment exists. Pending-commit panel captured (`docs/evidence/phase-b/`), closing the
  A7 evidence gap. Variable notes added and committed separately (`4bf75ed`).
- 2026-07-16 — B3 built and proven (**commit pending**). `pl_ingest_ree` in `orchestration`:
  5 String params (no defaults — a default would let a caller silently ingest the wrong
  window), `cp_fetch_json` Copy activity, REST connection `conn_ree_apidatos` (anonymous,
  base `https://apidatos.ree.es`), retry 3 × 60 s, `mail_failure` on the On-fail branch.
  **Outlook activity worked on the student tenant** — the anticipated Exchange-licensing
  blocker did not materialize, so no Teams fallback needed.
  Three findings the guide didn't predict, all now in its Gotchas: (1) the **Mapping tab must
  stay empty** or Copy reshapes the payload — left empty, and Bronze verified byte-faithful
  (raw response 2946 B vs landed file 2 KB, JSON:API envelope intact); (2) Fabric pre-populates
  a pagination rule **`RFC5988 = True`** which would concatenate `Link`-header pages into one
  file — probed the API, REE sends no `Link` header, so it's inert and left at default;
  (3) REE is behind an **Imperva WAF**, which makes `Sequential = ON` self-preservation rather
  than mere politeness — watch B7's early iterations for 403s. Library-variable syntax recorded:
  `@pipeline().libraryVariables.vl_energy_v_alert_email` (flattened, not nested).
  Idempotency proven at the unit level: identical re-run → 1 file, same name, timestamp
  2:39:22 → 2:42:54 (`docs/evidence/phase-b/`).
- 2026-07-16 — B3 committed (`021b0a4`) and mirrored; definition reviewed (satisfies part of
  B10 for this pipeline). Clean: params all String/no defaults, expressions intact,
  `"schema": []`/`{}` machine-confirming the Mapping tab stayed empty, retry 3 × 60 s,
  `mail_failure` gated on `["Failed"]`, **no secrets and no hardcoded email** — the recipient
  is a `libraryVariables` reference. **But two dev-tenant GUIDs are baked in** (`artifactId`
  = dev's `lh_energy`, `connection` = dev's REST connection): deployed verbatim to prod they'd
  resolve *silently* to dev's objects. This is **M3 made concrete in the repo** — the Phase F
  re-test is now "open this file and find what breaks" rather than a multiple-choice question,
  and `parameter.yml` has a documented, non-hypothetical job.
- 2026-07-16 — B4 done (hybrid flow exercised end to end). Shells created in Fabric (`6e496d2`),
  code written in the repo on `feature/ingest-notebooks`, reviewed and squash-merged via
  [PR #2](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/2) (`3fac95a`), pushed to
  `devops`, pulled into the workspace with *Update all*. **`bronze.ctl_watermark` created and
  bootstrapped** (`demanda_evolucion` / `2022-12-31T23:59` — deliberately before the backfill
  start so the first daily run has a floor). No errors. **`bronze` appeared as a genuine schema
  node** alongside `dbo` — the first Delta table in this lakehouse, and therefore the first real
  validation that A3's irreversible schemas checkbox does what M2 says (namespaces, and the
  Phase C MLV prerequisite). `updated_at` stored in UTC.
  Chunking logic verified locally before any of this: 129 chunks = 43 months × 3, contiguous,
  leap-year/year-roll correct, inverted range rejected.
  **Two findings from validating a generated chunk against the live API** (details in the guide's
  Gotchas — both reshape Phase C): (1) `time_trunc=hour` is **not honoured** for the spot price,
  which switched to **15-minute grain on 2025-01-01** — our backfill range straddles the cutover,
  so `fact_price` needs `period_minutes` as data rather than an assumption; (2) **DST is
  physically present** in the payloads (transition months carry both `+01:00` and `+02:00`;
  counts run −1/+1 hourly and −4/+4 quarter-hourly), so Silver's UTC normalization is load-bearing
  — local timestamp alone is not a unique business key, and "every day has 24 rows" would be
  wrong twice a year.
- 2026-07-16 — B5 built and committed (`d81de3d`). Blocker + decision: the new **Invoke pipeline**
  activity **requires a connection** (the guide assumed otherwise). Fabric ships two variants;
  chose the new one over Legacy because B7 fires 129 child runs at a WAF-fronted API and Legacy
  can only monitor the *parent* — created `conn_fabric_pipelines` with **Organizational account**
  auth. (Workspace identity **was** offered in the dropdown, contrary to my prediction — but the
  dropdown doesn't check prerequisites, and WI additionally needs a tenant setting plus a real
  F-SKU capacity, which trial isn't. **Track B probe:** on the own tenant + F2, WI is the better
  answer and removes the user-token dependency.)
  Definition reviewed: `isSequential` ✅, `waitOnCompletion` ✅, `@json(...exitValue)` ✅, all five
  `@item()` mappings ✅, three watermark activities all gated on `Succeeded` ✅ (M4 wired into the
  graph — if the loop dies the watermark never moves). **Bug caught by the review:** `nb_chunks`'s
  base parameters serialized as empty literals (`"value": ""`) instead of
  `@pipeline().parameters.p_from`/`p_to` — B7 would have died at the first activity with
  `ValueError: p_from must be a non-empty YYYY-MM-DD date`. That's the empty-defaults design
  working (loud failure, not a silent wrong range), but it needs fixing before B7. Fix in flight.
  All dev item/connection GUIDs collected into the table above rather than left for F2.
  `nb_chunks` params fixed (`b7a9eb1`).
- 2026-07-16/17 — B6 done, but **redesigned mid-build**. The planned Lookup on the SQL analytics
  endpoint is unusable: T-SQL Query (Preview) needs a connection kind the OneLake catalog picker
  can't produce, and the connection's only auth kind is OAuth 2.0, so the error asking us to
  change it has no remedy. Three attempts, then stopped (guide Gotchas).
  **Replaced with `nb_gen_chunks`** — one notebook, `p_mode` = `backfill`|`daily`
  ([PR #3](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/3), `25a5f9a`) — superseding
  `nb_gen_backfill_chunks` (retired `48be9de`). Better on the merits, not a workaround: no third
  connection, `INDICATORS` + `month_windows` in exactly one place, both pipelines the same shape,
  logic testable in Python. The Spark-cost argument that favoured the Lookup was **wrong** —
  `nb_update_watermark` is a notebook, so a Spark start was always in the daily path. M5 still
  gets demonstrated at **C7** (already planned).
  **This also fixed a latent bug in the specified design:** daily issued one request for
  `watermark → yesterday`, so any outage beyond a calendar month yields a window the API rejects —
  and since a failed run never advances the watermark, daily could never catch up unaided.
  Verified locally: 3-month outage → 12 chunks, none crossing a month; same-day re-run → 0 chunks,
  no error; lagging indicator resumes from its own watermark.
  Both pipelines reviewed post-commit: `p_mode` correct on each, `p_from`/`p_to` expressions
  survived the notebook swap, Sequential ✅, connections present on both `inv_ingest`, watermarks
  gated on `Succeeded`. **Next: B7 — run the backfill (129 chunks; the WAF question).**
- **2026-07-17 — B7 run + aftermath.** Backfill ran ~129 sequential child runs; **no WAF blocks**
  (Imperva never fired on the polite 1-request-at-a-time cadence). Local verifier: **129/129 OK**
  (structure, envelope, window bounds); first verifier pass reported 129× BAD_JSON — a bug in the
  *verifier* (opened `utf-8`, not `utf-8-sig`): REE sends no BOM (`7B 22 64`), **Fabric's JsonSink
  adds one**. Recorded as Phase C reader gotcha. The parent run then **failed at the watermark
  step**: three parallel Delta MERGEs into unpartitioned `bronze.ctl_watermark` →
  `ConcurrentAppendException` (Delta optimistic concurrency; commit-level conflict detection).
  Ledgered as **M6**. Chose serialization over partitioning/retry (3 tiny writes, simplicity wins).
  Repair: two manual `nb_update_watermark` runs (`generacion_estructura` bootstrapped,
  `demanda_evolucion` advanced) → 3 rows @ `2026-07-16T23:59`, verified via Spark SQL — the
  Lakehouse **table preview kept showing stale rows even after Refresh** (guide Gotchas; M5's
  sibling: read surfaces sync async, Delta log is the truth). Both pipelines rewired
  `fe_chunks → nb_wm_demanda → nb_wm_generacion → nb_wm_precios`, committed from Fabric
  (`0510dc2`), definitions verified in Git, mirrored. **Next: B8 — incremental + idempotent +
  kill-test; the daily run is also the concurrency-fix proof.**
- **2026-07-17 (evening) — B8 complete, but first: a data-loss bug caught pre-run.** Prepping B8
  exposed that daily mode's `watermark+1 → yesterday` window is *mid-month* while Bronze stores
  one whole-overwritten file per (indicator, month) — the first post-backfill daily run would
  have replaced July's complete file with a one-day fragment. Fixed in `nb_gen_chunks`
  (`ed4fbce`, month-boundary snap after the currency check; 5 scenarios verified locally;
  guide Gotchas has the full write-up). Then all four B8 proofs ran green: **B8a** no-op
  (`exitValue "[]"`, serialized `nb_wm_*` Gantt — the ConcurrentAppendException fix confirmed
  end-to-end); **B8b** 3-day simulated lag → exactly 1 month-to-date chunk, July file count
  unchanged/timestamp new; **B8c** cancel at 2m46s → identical-params re-run green 7m22s;
  **B8d** the backfill's designed watermark regression (`p_to` stamp → `06-30`) healed by one
  daily run (`07-16`) with zero manual repair. Actual full-backfill duration recorded:
  **3h53m49s** vs **3m42s** daily no-op — the portfolio contrast number. Both `b8d` shots also
  re-prove serialization independently: `updated_at` marches demanda → generacion → precios,
  ~55s apart. Evidence: 8 screenshots renamed + cataloged (`b8d-watermark-corrupted` →
  `…-regressed`: it's designed behavior, not corruption). **Next: B9 — schedule the daily run.**
- **2026-07-17 (night) — B9 + B10: Phase B closed.** M4 re-tested right after the kill-test and
  **closed** (1/1; rejected "watermark resume" with the original miss on the table — `815c519`).
  Schedule created (daily 08:00 Madrid, 07-18 → 07-30) and — the finding of the night — **it
  serialized into Git** as `pl_ingest_daily.DataPipeline/.schedules` (`f233aef`): dedicated
  gitIntegration JSON schema, `Romance Standard Time`, meaning schedules ride along in Phase F's
  fabric-cicd deploy instead of needing manual re-creation. B10 definition review **passed**
  (no secrets/emails, alert via library variable, Copy retry 3×60s, Sequential ForEach ×2,
  serialized watermark chains ×2, raw passthrough, `workspaceId` zeros). Non-blocking notes:
  12h default timeouts, notebooks retry 0, `supportRFC5988` default-true-but-inert, last
  scheduled firing Jul 30. **📣 Portfolio assets captured for the Phase C checkpoint:** the
  numbers (43 months × 3 indicators, 129/129 verified, **3h53m49s backfill vs 3m42s no-op /
  5m16s incremental**), the incident arc (`b7-backfill-run-failed-concurrency` →
  `b7-pipeline-serialized-chain` → `b8a-daily-noop-serialized`), the M4 arc
  (`b8c-*` kill-test pair → `b8d-watermark-regressed` → `b8d-watermark-selfhealed`), and the
  economics pair (`b8b-run-history-*`). Outstanding: `b9-scheduled-run-green.png` tomorrow
  (reminder task set, fires 08:15). **Next: Phase C — Transform & DQ, starting at C1
  (learn first: Delta, V-Order, partitioning, MLVs); M5 and M6 re-tests are due there.**
- **2026-07-18 — C1 + C1.5 done (Phase C opened).** C1 taught in-session (Gonzalo asked for the
  material in-chat rather than MS Learn links): Delta table = Parquet + `_delta_log` and why the
  log-vs-cache split explains Phase B's stale preview; schema enforcement (default, the free DQ
  wall) vs evolution (`mergeSchema`/`overwriteSchema`, opt-in); the V-Order (auto) /
  OPTIMIZE + VACUUM (manual) split with VACUUM's time-travel hazard; `.collect()` → driver OOM;
  the ~1 GB partition rule → no partitioning here; MLV (declarative, engine-refreshed) vs
  notebook aggregate (imperative, arbitrary logic). Medallion + DQ-gate flow diagrammed.
  **C1.5 🎓 = 6/6 — first perfect check**, both "automatic" distractors rejected. No new
  misconceptions. M5 (SQL endpoint read-only) and M6 (Delta concurrency) remain open — their
  live re-tests land at C7 and C4/C5 respectively, not at C1.5. **Next: C2 — build the
  `energy_lakehouse` package (parsers + DQ module + tests), branch `feature/dq-module`, PR to
  develop, then `uv build` the wheel for C3.**
- **2026-07-18 — C2 done: `energy_lakehouse` package built, tested, wheel'd.** Captured real
  REE samples live for fixtures (tokenless `apidatos.ree.es`, sequential — no WAF). Package
  (hatchling, `src/` layout): `parsers.py` (typed per-indicator parsers), `dq/checks.py` (pure
  null/range/freshness/row-count checks), `dq/gate.py` (write-then-raise, the only Spark-touching
  module), `models.py`, `indicators.py`. **Deliberately Spark-free at import** — verified by
  importing the wheel in an env with no pyspark. 24 pytest cases over captured fixtures;
  ruff + `mypy --strict` + pytest green; `ruff` scoped to exclude `fabric/` (notebooks aren't
  plain modules). Five REE-shape findings confirmed and coded (see phase-c guide Gotchas):
  composite-aggregate exclusion, `is_renewable` from the payload, civil-date-vs-UTC split,
  per-series price grain, structural-quarantine vs semantic-gate boundary.
  [PR #4](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/4) → `2c2ea00`, mirrored
  to devops (0/0). **Next: C3 `[YOU]` — Fabric Environment `env_energy` + wheel upload + publish
  + set workspace Spark default.**
- **2026-07-18 — C3 done: `env_energy` published, wheel uploaded, set as workspace Spark
  default.** Fabric committed the Environment (`f08e448`): `.platform`
  (logicalId `3b5f385e-8165-b78f-4b3a-72bf5981e359`, now in the Phase F IDs table),
  `Setting/Sparkcompute.yml`, and — notably — the **`.whl` binary itself** under
  `Libraries/CustomLibraries/` (14 KB in Git). That makes the Environment fully reproducible
  from source and deployable by fabric-cicd in Phase F, at the cost of a small tracked binary
  (acceptable; `*.whl` isn't globally gitignored, only `dist/`). Fast-forwarded + mirrored to
  origin (0/0). Gonzalo asked to be **proactively reminded to capture evidence screenshots** —
  saved as standing feedback. **Next: C4 — `[YOU]` create shells `silver/nb_bronze_to_silver`
  + `orchestration/nb_dq_gate`; then Claude writes both on `feature/silver-transform`.**
- **2026-07-19 — C4 closed: the gate caught real data, the fix shipped, the gate went green.**
  The arc in one line: first `nb_dq_gate` run **failed** on 8 negative `silver.generation_daily`
  rows → diagnosis showed all 8 are `Carbón` (thermal self-consumption, legitimate REE data,
  min −120 MWh across 3.5 years) → fix as a **versioned wheel release** (0.2.0, `48b0ff3`:
  renewable-aware bound `(is_renewable AND value<0) OR value<-1000`, demand kept strictly `>0`
  as the C5 signal, policy locked by two new tests) → wheel re-uploaded + `env_energy`
  re-published (Fabric commit `59441b2`, the `.whl` binary renamed 0.1.0→0.2.0 in Git) →
  re-run green: `ops.dq_results` latest `run_ts` = **20/20 PASS** (`c4-dq-gate-green.png`,
  with the status profile panel proving `Unique: 1`). Also today: Phase B fully closed
  (`b9-scheduled-run-green.png`; **Run kind** column, not "Submitted by", is the scheduled
  proof) and `docs/data-dictionary.md` added (units confirmed by profiling: MWh / MWh / €/MWh).
  The thin-notebook trade-off showed its cost knowingly: a threshold change = wheel rebuild +
  env re-publish (~10 min), the price of DQ policy being unit-tested code instead of a cell
  edit. **Next: C5 — corrupted-file test (quarantine + gate FAIL + restore).**
