# CLAUDE.md

## Project

Batch energy lakehouse on Microsoft Fabric (flagship, P1) plus the Real-Time
Intelligence extension under `streaming/` (P2). Plans:
`docs/fabric-p1-energy-lakehouse.md` and `docs/fabric-p2-realtime-intelligence.md`
(master: `fabric-portfolio-plan.md` in the workspace wiki).

**Execution state lives in `docs/phases/`** — one step-by-step guide per phase (P1:
`phase-*.md`, P2: `p2-phase-*.md`) with `[YOU]`/`[CLAUDE]` roles, plus **per-track
progress trackers** (`track-a-progress.md` / `track-b-progress.md`): P1 guides hold
instructions only; each track's tracker holds the checkboxes, per-phase status, and
session log for that run (P2 guides still carry inline checkboxes). At session start,
read the active tracker and the phase guide it points at; keep the tracker updated as
work progresses (conventions in `docs/phases/README.md`).

**Instructions to Gonzalo are always given in great detail** — exact portal paths,
button names, values to type, and how to verify the result, in the style of the
`[YOU]` steps in `docs/phases/`. This applies to ad-hoc guidance too, not just the
phase guides.

## Two-track execution — Git integration

The project runs the same P1 phases **twice** to demonstrate both Fabric Git providers
(definitions, remote layout and status: `docs/phases/tracks.md`):

- **Track A — Azure DevOps (active):** student tenant (GitHub provider blocked there);
  Fabric syncs with an Azure DevOps repo; **this GitHub repo stays canonical** via
  mirroring (`origin` = GitHub, `devops` = Azure DevOps).
- **Track B — GitHub (planned):** own tenant + credit-funded F2 capacity; native GitHub
  Git integration and SPN CI/CD.

**Mirror rule (vital):** phase guides serve both tracks — track-agnostic steps written
once, divergent steps as `[Track A]`/`[Track B]` variant blocks side by side. Any edit
touching one track's variant must review/update the sibling variant **in the same
commit**; the two tracks must always describe the same phases and end product.

## Branching — develop-flow

- `feature/*` branches off `develop`; PRs merge into `develop`.
- `develop` → `main` by PR only — `main` is the review gate; wait for explicit
  approval before merging.
- Fabric Git integration binds the dev workspace to `develop`; `main` deploys to the
  prod workspace via `fabric-cicd` (GitHub Actions).
- Conventional Commits (`type(scope): summary`); no AI attribution in commits or PRs.

## Rules

- Python follows the workspace standard (`.claude/rules/python.md`): ruff
  format/lint, `mypy --strict`, Google-style docstrings. Notebooks stay thin
  orchestration; typed helpers live in `src/`.
- Never commit secrets or data — `.env`, tokens and datasets are gitignored
  (ESIOS token included).
- Evidence pack as you go: item definitions as code, `docs/` notes, screenshots and a
  short recording. The trial workspace is ephemeral; the repo is the durable artifact.

## Standing objectives — portfolio, documentation, learning

These three run alongside every phase. Treat them as first-class deliverables, not
afterthoughts, and act on the checkpoints seeded in the phase guides.

1. **Portfolio.** This project is portfolio evidence. The portfolio site lives at
   `../../portfolio/astro` (Astro — English entries in `src/content/projects/*.mdx`,
   Spanish mirror in `src/content/projectsEs/`; an existing `azure-pipeline.mdx` is the
   closest format precedent). At the **📣 Portfolio** checkpoints in the phase guides,
   remind Gonzalo to update the entry (`fabric-energy-lakehouse.mdx`) and help draft it.
   Cadence: seed a draft at end of **Phase A**, add the engineering narrative at
   **Phase C**, add the Power BI showcase at **Phase E**, finalize (status, demo, links)
   at **Phase G**; P2 extends the same entry with the streaming section at **P2 Phase E**
   (assets captured at the 📣 points in P2 Phases B–D). Proactively flag portfolio-worthy
   moments even between checkpoints.
2. **Reproducible documentation.** Keep `docs/phases/` the truthful, step-by-step build
   journal (conventions in `docs/phases/README.md`): tick checkboxes, keep the status
   line and session log current, and record every deviation — the standard is that a
   cold reader could reproduce the build and that it presents as structured work.
3. **Learning.** A second purpose is fluency in Fabric for Gonzalo's job. At the
   **🎓 Learning** checkpoints (after each "Learn first" block), actively verify
   understanding before building on a concept: quiz with `AskUserQuestion`, draw
   pipeline/concept diagrams (`show_widget` / Mermaid), and pull authoritative sources
   with WebSearch. Don't just build it — make sure he can explain it cold; the P1 plan's
   interview drills are the bar.

**Keep adjacent artifacts current** (reminders live at phase ends): the workspace wiki
(`../../wiki` — `fabric-lakehouse` and `azure-fabric` learning notes) and the master CV
(`../../jobsearch/CVs/Master`) once the project has a presentable result.
