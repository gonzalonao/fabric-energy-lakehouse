# Phase execution guides

One file per phase — P1 (see [fabric-p1-energy-lakehouse.md](../fabric-p1-energy-lakehouse.md))
and P2 (see [fabric-p2-realtime-intelligence.md](../fabric-p2-realtime-intelligence.md);
files prefixed `p2-`). Each file is the **single source of truth for that phase**: the
exact steps to follow, who does each one, what has been done, and what went wrong. A
fresh Claude session should be able to resume work from these files alone.

The project runs **two execution tracks** (A = Azure DevOps on the student tenant,
B = GitHub on an own tenant) over the same phases — see [tracks.md](tracks.md) for
definitions, the git mirroring layout, and the **mirror rule**: divergent steps appear
as `[Track A]`/`[Track B]` variant blocks inside the same phase file, and an edit to one
variant must keep its sibling consistent in the same commit.

**Progress is recorded per track**, not in the guides: P1 phase guides hold the
*instructions* (plain bullets, no checkboxes); each run ticks its own checklist in
[track-a-progress.md](track-a-progress.md) / [track-b-progress.md](track-b-progress.md)
— per-step checkboxes, per-phase status, done-criteria, and that track's session log.
(P2 guides still carry inline checkboxes — single-run until a track is chosen.)

## Conventions

- **`[YOU]`** — manual steps Gonzalo performs (Fabric portal, GitHub UI, screenshots).
- **`[CLAUDE]`** — steps Claude performs locally (repo files, git, code review, docs).
- **📣 Portfolio** — a checkpoint to add/update the portfolio entry at
  `../../portfolio/astro` (`src/content/projects/fabric-energy-lakehouse.mdx`).
- **🎓 Learning** — a checkpoint where Claude actively checks understanding (quiz,
  diagram, authoritative sources) before the work builds on a new Fabric concept.
- Steps are numbered `A1, A2, …` per phase and ordered — do them top to bottom;
  interleaving matters (e.g. Claude can't verify a sync before you commit it).
- **Progress lives in the track trackers** (`track-a-progress.md` / `track-b-progress.md`
  for P1): tick the step there as it completes — Claude updates the tracker when told a
  `[YOU]` step is done, and after finishing its own steps. P2 guides keep inline
  checkboxes for now.
- Per-phase status (`⬜ · 🔄 (at step X) · ✅`) lives in the tracker next to each phase
  heading, plus a top-level Status line per tracker.
- **Session log** at the bottom of each tracker: one dated line per working session with
  what was completed and any deviation from the written steps. Deviations also get a
  bullet under the phase guide's *Gotchas & deviations* so the steps stay truthful.
- To resume in a new session, tell Claude:
  *"Read docs/phases/track-<a|b>-progress.md — we're at step <n>."*

## Files

### P1 — Energy lakehouse (D1–D7)

| Phase | File | Days | Status |
|---|---|---|---|
| A — Platform & Git | [phase-a-platform-git.md](phase-a-platform-git.md) | D1 | 🔄 |
| B — Batch ingestion | [phase-b-batch-ingestion.md](phase-b-batch-ingestion.md) | D2–D3 | ⬜ |
| C — Transform & DQ | [phase-c-transform-dq.md](phase-c-transform-dq.md) | D3–D5 | ⬜ |
| D — Orchestration | [phase-d-orchestration.md](phase-d-orchestration.md) | D5 (+2 passive) | ⬜ |
| E — Serving | [phase-e-serving.md](phase-e-serving.md) | D6 | ⬜ |
| F — CI/CD | [phase-f-cicd.md](phase-f-cicd.md) | D6–D7 | ⬜ |
| G — Evidence & docs | [phase-g-evidence-docs.md](phase-g-evidence-docs.md) | D7 | ⬜ |

### P2 — Real-Time Intelligence (D8–D11)

| Phase | File | Days | Status |
|---|---|---|---|
| A — KQL foundations | [p2-phase-a-kql-foundations.md](p2-phase-a-kql-foundations.md) | D8 (half) | ⬜ |
| B — Stream ingestion | [p2-phase-b-stream-ingestion.md](p2-phase-b-stream-ingestion.md) | D8–D9 | ⬜ |
| C — KQL analytics + dashboard | [p2-phase-c-kql-analytics-dashboard.md](p2-phase-c-kql-analytics-dashboard.md) | D9–D10 | ⬜ |
| D — Activator | [p2-phase-d-activator.md](p2-phase-d-activator.md) | D10 | ⬜ |
| E — Unification + evidence | [p2-phase-e-unification-evidence.md](p2-phase-e-unification-evidence.md) | D11 | ⬜ |
