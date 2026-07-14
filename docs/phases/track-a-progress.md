# Track A — progress (Azure DevOps · student tenant)

**This file is the single progress record for Track A.** Instructions live in the phase
guides (`phase-*.md`); steps marked `[Track B]` there don't apply here. Sibling tracker:
[track-b-progress.md](track-b-progress.md) · definitions: [tracks.md](tracks.md).

**Tenant/capacity:** ESESA/UCAM student tenant · Fabric trial capacity ·
window ends ~2026-07-31.
**Git:** Fabric ↔ Azure DevOps repo (`develop`, `/fabric`); GitHub canonical via mirror.
**Status:** 🔄 Phase A at A11 (🎓 understanding check, then A12 📣 portfolio seed).
A1–A10 done — all three Phase A done-criteria met; evidence pack captured.
**DevOps:** org `glopezc443` · project/repo `fabric-energy-lakehouse` · remote `devops`
(`https://dev.azure.com/glopezc443/fabric-energy-lakehouse/_git/fabric-energy-lakehouse`).
**Dev workspace GUID:** `476b58fd-19e3-4c0d-bde7-c3f16d2a6fcf`.

## Phase A — Platform & Git · [guide](phase-a-platform-git.md) · 🔄

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
- [ ] A11 — 🎓 Git-integration understanding check
- [ ] A12 — 📣 portfolio entry seeded

Done criteria:
- [x] Commit made from Fabric visible on `develop` *(`ca6ccdd` lakehouse, `826232f`
      notebook — mirrored to GitHub)*
- [x] Workspace folder structure in place *(`a2-folders-lakehouse.png`)*
- [x] Notebook round-trips as `.py` with readable PR diff *(PR #1 — `a8-pr-diff.png`;
      pulled back into Fabric — `a9-notebook-select2.png`)*

## Phase B — Batch ingestion · [guide](phase-b-batch-ingestion.md) · ⬜

- [ ] B1 — learn first (pipelines, Copy vs Web, variable libraries)
- [ ] B1.5 — 🎓 ingestion & watermark check
- [ ] B2 — variable library `vl_energy`
- [ ] B3 — core pipeline `pl_ingest_ree` (+ unit idempotency proof)
- [ ] B4 — watermark + chunking notebooks (hybrid flow)
- [ ] B5 — backfill pipeline `pl_backfill_ree`
- [ ] B6 — daily pipeline `pl_ingest_daily`
- [ ] B7 — backfill run 2023-01 → now
- [ ] B8 — incremental + idempotent + kill-test proofs
- [ ] B9 — daily schedule active
- [ ] B10 — review + evidence + 📣 asset capture

Done criteria:
- [ ] Backfill loaded for all three indicators
- [ ] Incremental run fetches only new dates (screenshots)
- [ ] Killed run re-runs idempotently
- [ ] Schedule + failure alert wired

## Phase C — Transform & DQ · [guide](phase-c-transform-dq.md) · ⬜

- [ ] C1 — learn first (Delta, V-Order, partitioning, MLVs)
- [ ] C1.5 — 🎓 Delta/DQ/MLV check
- [ ] C2 — `energy_lakehouse` package + DQ module + tests + wheel
- [ ] C3 — Fabric environment `env_energy` with the wheel
- [ ] C4 — silver + DQ-gate notebooks; units confirmed
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
