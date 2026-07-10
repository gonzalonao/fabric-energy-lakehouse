# Phase G — Evidence & docs

**Status:** ⬜ not started
**Days:** D7 · **Plan:** [P1 §Phase G](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phases A–F ✅ (this phase packages them)

## Outcome (done criteria)

- [ ] README is recruiter-ready per the portfolio standard (`github/CLAUDE.md`):
      architecture Mermaid, data dictionary link, run instructions, tech badges,
      LinkedIn/GitHub links.
- [ ] `docs/decisions.md` — consolidated decision log with rationale.
- [ ] Capacity Metrics screenshots + CU-cost notes per workload
      (`docs/capacity-notes.md`).
- [ ] 60–90 s demo recording linked from the README.
- [ ] Wiki: `fabric-lakehouse` note created; `azure-fabric` corrected.
- [ ] Interview drills done out loud, gaps noted.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Recording format | MP4, target < 10 MB (1080p, short). If larger: attach to the `v1.0.0` GitHub release and link from README — **never** a large binary in the repo | Workspace rule: no large binaries in git |
| Evidence timing | This phase only *assembles* — screenshots were captured per phase as work happened (the workspace dies in August; nothing can be re-captured later) | Master-plan rule; if something is missing, capture it NOW while the trial lives |
| Wiki vs repo docs | Repo docs = what a recruiter reads (architecture, decisions, costs). Wiki = what future-Gonzalo reads (gotchas, drill answers, patterns) | Different audiences, different homes |

## Steps

### G1 `[CLAUDE]` README overhaul

- [ ] Rewrite `README.md` per the portfolio README standard:
  - One-sentence description + tech badges (Fabric, PySpark/Delta, Data Factory,
    Power BI Direct Lake, fabric-cicd, GitHub Actions).
  - **Mermaid architecture diagram**: REE API → `pl_ingest_ree` (watermark) → Bronze
    Files → Silver Delta (+ DQ gate + quarantine) → Gold star schema (+ MLVs) →
    Direct Lake `sm_energy` → `rpt_energy`; side lane: Git ↔ dev workspace,
    `main` → fabric-cicd → prod.
  - What it demonstrates (map to DP-700 topics), honest constraints paragraph
    (trial capacity, SPN outcome from F1, MLV/preview caveats).
  - Run instructions: local setup (`uv sync`, tests), deploy
    (`scripts/deploy.py`), links to `docs/phases/` as the build journal.
  - Links: data dictionary, decisions log, demo recording, LinkedIn + GitHub profile.
- [ ] PR → merge (README readable on the GitHub repo front page — check rendering).

### G2 `[CLAUDE]` Consolidated decision log

- [ ] `docs/decisions.md`: merge every phase file's Decisions table + the material
      Gotchas entries into one chronological log (date, decision, why, outcome).
      Source phases stay untouched — this is the reading copy.

### G3 `[YOU]` + `[CLAUDE]` Capacity metrics (cost awareness — reads senior)

- [ ] `[YOU]` Install the **Microsoft Fabric Capacity Metrics** app (you're capacity
      admin): app.fabric → Apps → Get apps → search "Capacity Metrics" → install →
      point it at the trial capacity.
- [ ] `[YOU]` Screenshots: CU consumption by item over the sprint week — identify the
      top consumers (expect: Spark notebooks > pipelines > Direct Lake queries);
      the backfill day vs a steady-state day; any throttling/smoothing events.
- [ ] `[CLAUDE]` `docs/capacity-notes.md`: per-workload CU observations, what would
      change on a paid F-SKU (which size fits this workload and why), smoothing in one
      paragraph (drill answer material).

### G4 `[YOU]` Demo recording (60–90 s)

- [ ] Script (rehearse once, record with Windows `Win+Alt+R` or OBS):
  1. (~15 s) Repo front page — README architecture diagram.
  2. (~20 s) `ws-energy-dev`: run history of `pl_daily_refresh` (green days),
     open the run detail showing the DQ gate stage.
  3. (~20 s) `rpt_energy`: interact — demand trend, renewables share, price panel.
  4. (~15 s) A notebook PR diff on GitHub + the prod workspace item list
     (deployed by CI, untouched by hand).
- [ ] Keep it silent (no mic needed) — motion + captions carry it.
- [ ] Hand the file to Claude → `[CLAUDE]` compress if needed, place/link per the
      Decisions row, commit.

### G5 `[CLAUDE]` Wiki notes (workspace wiki, not this repo)

- [ ] Create `wiki/learning/fabric-lakehouse.md`: gotchas harvested from every phase
      file's Gotchas section, patterns that worked (hybrid notebook flow, watermark
      design, DQ gate shape), and **written-out answers to all ten interview drills**
      from the P1 plan (house rule: write for a future you who forgot everything).
- [ ] Update `wiki/learning/azure-fabric.md` with corrections discovered during the
      sprint (schema-enabled lakehouse notes, Direct Lake fallback, MLV reality vs
      docs).
- [ ] Update wiki `learning/index.md` with the new note.

### G6 `[YOU]` Interview drills (no notes, out loud)

- [ ] Run the drill list from [the P1 plan](../fabric-p1-energy-lakehouse.md#interview-drills-no-notes-out-loud)
      out loud, cold. Mark any that stumbled: ______
- [ ] Stumbled ones: re-read the wiki note (G5), repeat tomorrow morning.

### G7 `[YOU]` + `[CLAUDE]` Final gate — evidence pack checklist (master plan §Evidence)

- [ ] 1. Item definitions as code in `fabric/` — complete for every item in dev.
- [ ] 2. `docs/`: architecture ✓ decisions ✓ capacity notes ✓ data dictionary ✓.
- [ ] 3. Screenshots per phase in `docs/evidence/` + demo recording linked.
- [ ] 4. Wiki note exists and is honest.
- [ ] `[CLAUDE]` Set every phase file + the phases README index to final status;
      last session-log entries; final commit. **P1 closed — P2 starts from
      [fabric-p2-realtime-intelligence.md](../fabric-p2-realtime-intelligence.md).**

### G8 `[CLAUDE]` + `[YOU]` 📣 Portfolio finalize + CV + wiki

- [ ] `[CLAUDE]` Final pass on `fabric-energy-lakehouse.mdx` (+ Es mirror): flip
      `status` to `"completed"`, set `featured`/`order` for prominence, link the demo
      recording and the GitHub repo, and make sure the architecture diagram + DQ-gate +
      Direct Lake + CI/CD story is coherent end-to-end. This is the same architecture
      Mermaid and narrative as the README (G1) — reuse, don't reinvent.
- [ ] `[YOU]` Review, commit, and deploy the portfolio site (Vercel picks up the push).
- [ ] `[CLAUDE]` Update the master CV (`../../jobsearch/CVs/Master`): add the project as
      a portfolio bullet — Fabric medallion lakehouse, DQ gate, Direct Lake, fabric-cicd
      CI/CD — with the DP-700-relevant keywords. `[YOU]` confirm phrasing.
- [ ] `[CLAUDE]` Confirm the wiki notes from G5 are in place; add a one-line pointer from
      the wiki learning index to the finished project if not already there.

## Gotchas & deviations

*(expected suspects: Capacity Metrics app needs a few hours of data lag; recording
size vs quality)*

## Session log

*(one dated line per session)*
