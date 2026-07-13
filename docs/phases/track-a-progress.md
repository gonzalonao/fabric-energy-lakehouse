# Track A — progress (Azure DevOps · student tenant)

**This file is the single progress record for Track A.** Instructions live in the phase
guides (`phase-*.md`); steps marked `[Track B]` there don't apply here. Sibling tracker:
[track-b-progress.md](track-b-progress.md) · definitions: [tracks.md](tracks.md).

**Tenant/capacity:** ESESA/UCAM student tenant · Fabric trial capacity ·
window ends ~2026-07-31.
**Git:** Fabric ↔ Azure DevOps repo (`develop`, `/fabric`); GitHub canonical via mirror.
**Status:** 🔄 Phase A at A4 (create the DevOps org).

## Phase A — Platform & Git · [guide](phase-a-platform-git.md) · 🔄

- [ ] A1 — two workspaces on trial capacity *(reported done 2026-07-13 — Large semantic
      model format, template apps off; tick after confirmation)*
- [ ] A2 — folders `bronze/silver/gold/orchestration` *(reported done — confirm)*
- [ ] A3 — lakehouse `lh_energy`, **schemas enabled** *(reported done — confirm the
      schemas checkbox was ticked)*
- [ ] A4 — `[Track A]` DevOps org + project + repo import
- [ ] A5 — bind `ws-energy-dev` ↔ `develop` (`/fabric`)
- [ ] A6 — verify sync landed; add `devops` remote; mirror to GitHub
- [ ] A7 — smoke-test notebook committed from Fabric
- [ ] A8 — `.py` round-trip PR on GitHub; push merge to `devops`
- [ ] A9 — Update all in Fabric; edit visible
- [ ] A10 — evidence captured + committed
- [ ] A11 — 🎓 Git-integration understanding check
- [ ] A12 — 📣 portfolio entry seeded

Done criteria:
- [ ] Commit made from Fabric visible on `develop`
- [ ] Workspace folder structure in place
- [ ] Notebook round-trips as `.py` with readable PR diff

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
