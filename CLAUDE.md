# CLAUDE.md

## Project

Batch energy lakehouse on Microsoft Fabric (flagship, P1) plus the Real-Time
Intelligence extension under `streaming/` (P2). Plans:
`docs/fabric-p1-energy-lakehouse.md` and `docs/fabric-p2-realtime-intelligence.md`
(master: `fabric-portfolio-plan.md` in the workspace wiki).

**Execution state lives in `docs/phases/`** — one step-by-step guide per phase with
`[YOU]`/`[CLAUDE]` roles, checkboxes, and a session log. At session start, read the
active phase file; keep its checkboxes, status line, and session log updated as work
progresses (conventions in `docs/phases/README.md`).

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
