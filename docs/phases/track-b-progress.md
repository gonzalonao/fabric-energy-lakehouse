# Track B — progress (GitHub · own tenant + F2)

**This file is the single progress record for Track B.** Instructions live in the phase
guides (`phase-*.md`); steps marked `[Track A]` there don't apply here. Sibling tracker:
[track-a-progress.md](track-a-progress.md) · definitions: [tracks.md](tracks.md).

**Tenant/capacity:** own Entra tenant (Azure free account) · **paid F2** funded by the
$200/30-day credit — pause when idle; never upgrade to pay-as-you-go.
**Git:** Fabric ↔ GitHub (this repo) natively; SPN + GitHub Actions CI/CD in Phase F.
**Status:** ⬜ not started — kickoff gate below must pass first.

## Kickoff gate (before any phase work — probe cheap things first)

- [ ] K1 — Azure free account created (card = identity check; €1 hold refunded)
- [ ] K2 — own Entra tenant confirmed (Global Admin)
- [ ] K3 — **probe Power BI Pro/individual trial availability on the fresh tenant**
      *(known risk — if blocked, Phase E is stuck; resolve before spending credit)*
- [ ] K4 — F2 capacity created, pause/resume verified, budget alert set
- [ ] K5 — tenant settings: GitHub Git provider enabled; Fabric enabled for the org
- [ ] K6 — repo strategy decided (reuse `/fabric` vs branch/folder split — item GUIDs
      differ from Track A; see tracks.md open questions)
- [ ] K7 — 30-day execution calendar drafted (credit clock starts at signup)

## Phase A — Platform & Git · [guide](phase-a-platform-git.md) · ⬜

- [ ] A1 — two workspaces on the F2 capacity
- [ ] A2 — folders `bronze/silver/gold/orchestration`
- [ ] A3 — lakehouse `lh_energy`, **schemas enabled**
- [ ] A4 — `[Track B]` GitHub fine-grained PAT
- [ ] A5 — bind `ws-energy-dev` ↔ `develop` (`/fabric`), provider **GitHub**
- [ ] A6 — verify sync landed (plain `git pull`)
- [ ] A7 — smoke-test notebook committed from Fabric
- [ ] A8 — `.py` round-trip PR on GitHub
- [ ] A9 — Update all in Fabric; edit visible
- [ ] A10 — evidence captured + committed
- [ ] A11 — 🎓 Git-integration understanding check *(delta vs Track A: compare providers)*
- [ ] A12 — 📣 portfolio entry: add the provider-comparison angle

Done criteria:
- [ ] Commit made from Fabric visible on `develop`
- [ ] Workspace folder structure in place
- [ ] Notebook round-trips as `.py` with readable PR diff

## Phase B — Batch ingestion · [guide](phase-b-batch-ingestion.md) · ⬜

*All code/pipeline definitions exist from Track A — this run is portal re-build +
re-sync, expected much faster.*

- [ ] B1 — learn first *(skim only — done in Track A)*
- [ ] B1.5 — 🎓 check *(only if Track A left weak spots)*
- [ ] B2 — variable library `vl_energy`
- [ ] B3 — core pipeline `pl_ingest_ree` (+ unit idempotency proof)
- [ ] B4 — watermark + chunking notebooks
- [ ] B5 — backfill pipeline `pl_backfill_ree`
- [ ] B6 — daily pipeline `pl_ingest_daily`
- [ ] B7 — backfill run (watch F2 headroom — smaller than trial capacity)
- [ ] B8 — incremental + idempotent + kill-test proofs
- [ ] B9 — daily schedule active *(pause discipline: schedule vs paused capacity —
      note CU behavior)*
- [ ] B10 — review + evidence

Done criteria:
- [ ] Backfill loaded for all three indicators
- [ ] Incremental run fetches only new dates
- [ ] Killed run re-runs idempotently
- [ ] Schedule + failure alert wired

## Phase C — Transform & DQ · [guide](phase-c-transform-dq.md) · ⬜

- [ ] C1 / C1.5 — learn + 🎓 *(skim/skip if solid from Track A)*
- [ ] C2 — package + wheel *(reuse artifact from Track A)*
- [ ] C3 — environment `env_energy` with the wheel
- [ ] C4 — silver + DQ-gate notebooks
- [ ] C5 — corrupted-file test
- [ ] C6 — gold star schema + MLVs
- [ ] C7 — SQL proofs
- [ ] C8 — wrap-up
- [ ] C9 — 📣 portfolio note (only deltas vs Track A)

Done criteria: *(same five as Track A — see [guide](phase-c-transform-dq.md))*
- [ ] All five met

## Phase D — Orchestration · [guide](phase-d-orchestration.md) · ⬜

- [ ] D1 — master pipeline `pl_daily_refresh`
- [ ] D2 — schedule moved to master
- [ ] D3 — two-day green proof
- [ ] D4 — review + evidence

Done criteria:
- [ ] All four met (see guide)

## Phase E — Serving · [guide](phase-e-serving.md) · ⬜

*Requires K3 green (Power BI licensing on the fresh tenant).*

- [ ] E1 / E1.5 — learn + 🎓 *(skip if airtight from Track A)*
- [ ] E2 — custom semantic model `sm_energy`
- [ ] E3 — relationships, date table, Direct Lake only
- [ ] E4 — DAX measures
- [ ] E5 — 3-page report `rpt_energy`
- [ ] E6 — Direct Lake verification *(F2 guardrails are lower than F64 — verify no
      fallback at our data size)*
- [ ] E7 — sync + TMDL review
- [ ] E8 — 📣 portfolio

Done criteria:
- [ ] All three met (see guide)

## Phase F — CI/CD · [guide](phase-f-cicd.md) · ⬜

*Track B is where the REAL SPN + GitHub Actions path runs — this is the headline delta.*

- [ ] F1 — SPN app registration (should work — own tenant)
- [ ] F2 — IDs + prod value set
- [ ] F3 — deploy code *(exists from Track A — adapt GUIDs/params)*
- [ ] F4 — branch protection
- [ ] F5 — gated promotion PR
- [ ] F6 — deploy via **GitHub Actions with SPN secrets**
- [ ] F7 — prod verified untouched-by-hand
- [ ] F8 — wrap-up + 🎓 check (SPN vs user-auth comparison, from experience)

Done criteria:
- [ ] Merge to `main` fires Actions → prod reproduced, no hands
- [ ] Rest per guide

## Phase G — Evidence & docs · [guide](phase-g-evidence-docs.md) · ⬜

- [ ] G1–G8 — as per guide; portfolio/README additions focus on the **two-track
      comparison** (DevOps vs GitHub integration, user-auth vs SPN deploys)

Done criteria:
- [ ] Per guide + comparison section published

## Session log (Track B)

*(one dated line per session — starts at kickoff)*
