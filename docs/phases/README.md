# Phase execution guides

One file per P1 phase (see [fabric-p1-energy-lakehouse.md](../fabric-p1-energy-lakehouse.md)).
Each file is the **single source of truth for that phase**: the exact steps to follow, who
does each one, what has been done, and what went wrong. A fresh Claude session should be
able to resume work from these files alone.

## Conventions

- **`[YOU]`** — manual steps Gonzalo performs (Fabric portal, GitHub UI, screenshots).
- **`[CLAUDE]`** — steps Claude performs locally (repo files, git, code review, docs).
- **📣 Portfolio** — a checkpoint to add/update the portfolio entry at
  `../../portfolio/astro` (`src/content/projects/fabric-energy-lakehouse.mdx`).
- **🎓 Learning** — a checkpoint where Claude actively checks understanding (quiz,
  diagram, authoritative sources) before the work builds on a new Fabric concept.
- Steps are numbered `A1, A2, …` per phase and ordered — do them top to bottom;
  interleaving matters (e.g. Claude can't verify a sync before you commit it).
- Checkboxes track progress. **Tick them as steps complete** — Claude updates the file
  when told a `[YOU]` step is done, and after finishing its own steps.
- The `Status` line at the top of each file is one of:
  `⬜ not started · 🔄 in progress (at step X) · ✅ done`.
- **Session log** at the bottom of each file: one dated line per working session with
  what was completed and any deviation from the written steps. Deviations also get a
  bullet under *Gotchas & deviations* so the steps stay truthful.
- To resume in a new session, tell Claude:
  *"Read docs/phases/phase-<x>.md — we're at step <n>."*

## Files

| Phase | File | Days | Status |
|---|---|---|---|
| A — Platform & Git | [phase-a-platform-git.md](phase-a-platform-git.md) | D1 | ⬜ |
| B — Batch ingestion | [phase-b-batch-ingestion.md](phase-b-batch-ingestion.md) | D2–D3 | ⬜ |
| C — Transform & DQ | [phase-c-transform-dq.md](phase-c-transform-dq.md) | D3–D5 | ⬜ |
| D — Orchestration | [phase-d-orchestration.md](phase-d-orchestration.md) | D5 (+2 passive) | ⬜ |
| E — Serving | [phase-e-serving.md](phase-e-serving.md) | D6 | ⬜ |
| F — CI/CD | [phase-f-cicd.md](phase-f-cicd.md) | D6–D7 | ⬜ |
| G — Evidence & docs | [phase-g-evidence-docs.md](phase-g-evidence-docs.md) | D7 | ⬜ |
