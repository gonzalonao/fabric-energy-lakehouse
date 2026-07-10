# Phase A — Platform & Git

**Status:** ⬜ not started
**Days:** D1 (≈ 2026-07-11) · **Plan:** [P1 §Phase A](../fabric-p1-energy-lakehouse.md)

## Outcome (done criteria)

- [ ] A commit made from Fabric appears on `develop` in this repo.
- [ ] Workspace folder structure `bronze / silver / gold / orchestration` in place.
- [ ] A notebook round-trips as `.py`: readable line-by-line diff in a PR, and an edit
      made in the repo shows up back in the Fabric notebook.

## Decisions (made up front — revisit only with a reason)

| Decision | Choice | Why |
|---|---|---|
| Lakehouse layout | **One schema-enabled lakehouse `lh_energy`** (schemas `bronze`/`silver`/`gold`), not one lakehouse per layer | One SQL endpoint for everything; materialized lake views (Phase C) require a schema-enabled lakehouse; fewer items on a 64 CU trial |
| Workspace folders | `bronze`, `silver`, `gold`, `orchestration` hold **notebooks/pipelines** per layer; `lh_energy` sits at workspace root | The lakehouse spans layers, so it belongs to none |
| Git sync folder | `/fabric` in this repo | Keeps Fabric item definitions out of the repo root, away from `docs/` and `src/` |
| Prod workspace | `ws-energy-prod` stays **empty and unbound** until Phase F | It is populated exclusively by `fabric-cicd` from `main`; never hand-edit it |
| GitHub auth for Fabric | Fine-grained PAT scoped to this single repo | Least privilege; trial ends ~2026-07-31 so expiry can be short |

## Steps

### A1 `[YOU]` Create the two workspaces

- [ ] Go to `https://app.fabric.microsoft.com` and sign in with the trial account.
- [ ] Left nav → **Workspaces** → **+ New workspace**.
- [ ] Name: `ws-energy-dev`. Expand **Advanced** → **License mode** → select
      **Trial** → **Apply**.
- [ ] Repeat for `ws-energy-prod` (also on Trial capacity). Do nothing else in prod.
- [ ] Sanity check: both workspaces show the trial diamond icon in the workspace list.

### A2 `[YOU]` Folder structure in `ws-energy-dev`

- [ ] Open `ws-energy-dev` → toolbar **+ New folder** → create, one by one:
      `bronze`, `silver`, `gold`, `orchestration`.

### A3 `[YOU]` Create the lakehouse

- [ ] In `ws-energy-dev` (workspace root, **not** inside a folder) → **+ New item** →
      **Lakehouse** → name `lh_energy`.
- [ ] **Tick the "Lakehouse schemas" checkbox** (public preview) before creating —
      this cannot be changed afterwards and Phase C's materialized lake views need it.
- [ ] Verify: open the lakehouse — the Tables tree shows a `dbo` schema node (schema
      mode active) and there is a Files section.

### A4 `[YOU]` GitHub fine-grained PAT for Fabric

- [ ] GitHub → **Settings → Developer settings → Fine-grained tokens → Generate new
      token**.
- [ ] Name `fabric-git-integration`; expiration **2026-08-15** (past trial end).
- [ ] Repository access: **Only select repositories** → `gonzalonao/fabric-energy-lakehouse`.
- [ ] Permissions → Repository permissions → **Contents: Read and write**
      (Metadata: Read is added automatically).
- [ ] Generate and copy the token. It goes **nowhere near this repo** — paste it only
      into the Fabric connection dialog in A5 (keep it in your password manager until then).

### A5 `[YOU]` Bind `ws-energy-dev` ↔ `develop`

- [ ] `ws-energy-dev` → **Workspace settings** → **Git integration**.
- [ ] Provider: **GitHub** → **Add account** → paste the PAT from A4 → connect.
- [ ] Repository: `gonzalonao/fabric-energy-lakehouse` · Branch: **`develop`** ·
      Git folder: **`/fabric`**.
- [ ] **Connect and sync.** The repo has no `/fabric` folder yet, so Fabric will offer
      to commit the workspace content into the branch — accept (direction:
      workspace → Git).
- [ ] Verify: the workspace header shows the branch name / **Source control** button
      with `0` pending changes.

### A6 `[CLAUDE]` Verify the sync landed in the repo

- [ ] `git pull` on `develop`; confirm `fabric/lh_energy.Lakehouse/` exists (a
      `.platform` metadata file — item definitions only, never data).
- [ ] Confirm `.gitignore` does not swallow anything under `fabric/`.
- [ ] Note in the session log what Fabric actually committed (item list).

### A7 `[YOU]` Round-trip test notebook

- [ ] In `ws-energy-dev` → open folder `orchestration` → **+ New item** → **Notebook**
      → name `nb_smoke_test`.
- [ ] Attach `lh_energy` as the default lakehouse (Explorer pane → Add data items → existing
      lakehouse).
- [ ] Single cell: `spark.sql("SELECT 1 AS smoke").show()` — run it once (first Spark
      session on the trial takes a minute or two; that's normal).
- [ ] Workspace → **Source control** (top right) → the notebook shows as a change →
      **Commit** with message `feat(platform): add smoke-test notebook`.

### A8 `[CLAUDE]` Verify `.py` round-trip and PR diff

- [ ] `git pull` on `develop`; confirm
      `fabric/nb_smoke_test.Notebook/notebook-content.py` is readable Python with cell
      markers (`# CELL ********************`).
- [ ] Create branch `feature/git-roundtrip-check`; edit the notebook `.py` (add a
      comment line and change `SELECT 1` to `SELECT 2`); push; open a PR into `develop`.
- [ ] Verify the PR diff renders as a clean line-level Python diff (screenshot-worthy —
      this is the "notebooks are reviewable" portfolio claim). Merge the PR.

### A9 `[YOU]` Pull the change back into Fabric

- [ ] `ws-energy-dev` → **Source control** → **Updates** tab → **Update all**.
- [ ] Open `nb_smoke_test` → confirm the edit from A8 is there (`SELECT 2` + comment).

### A10 `[YOU]` + `[CLAUDE]` Evidence capture

- [ ] `[YOU]` Screenshots → drop them in `docs/evidence/phase-a/` (any filenames):
  - [ ] Workspace list showing `ws-energy-dev` + `ws-energy-prod` on trial capacity.
  - [ ] Git integration settings page (connected repo/branch/folder visible).
  - [ ] Source control panel mid-commit (A7).
  - [ ] The PR diff of the notebook (A8) — from GitHub.
  - [ ] Workspace item view showing the four folders + lakehouse.
- [ ] `[CLAUDE]` Normalize filenames (`a1-workspaces.png`, …), commit evidence, tick the
      done-criteria boxes above, set Status ✅, append the session log.

### A11 `[CLAUDE]` 🎓 Understanding check — Git integration

- [ ] Before closing the phase, Claude quizzes Gonzalo (`AskUserQuestion`) on the
      concepts this phase exercised: what Fabric Git integration binds (workspace ↔
      branch/folder), why a notebook stored as `.py` (not `.ipynb`) is the thing that
      makes it reviewable in a PR, and dev-branch (`develop`) vs prod-deploy (`main` +
      fabric-cicd) direction. Draw the sync topology as a small diagram if it helps.
- [ ] Note any shaky answers here so they resurface in the Phase G interview drills.

### A12 `[CLAUDE]` + `[YOU]` 📣 Portfolio — seed the entry

- [ ] `[CLAUDE]` Create a **draft** portfolio entry
      `../../portfolio/astro/src/content/projects/fabric-energy-lakehouse.mdx`
      (+ Spanish mirror in `projectsEs/`): title, one-line summary, tech tags,
      `status: "in-progress"`, and a placeholder architecture Mermaid. Match the shape of
      the existing `azure-pipeline.mdx`. Keep `featured`/`order` conservative until it
      ships.
- [ ] `[YOU]` Skim the draft, adjust wording/voice, and decide whether to show it as WIP
      now or hold it unlisted until Phase G. (Reminder: the full write-up lands at 📣 in
      Phases C, E, G — this is just the stub so the entry exists.)

## Gotchas & deviations

*(append as encountered — UI names drift in preview features; if a step doesn't match
what you see, note here what it actually looked like)*

## Session log

*(one dated line per session — e.g. `2026-07-11 — A1–A5 done; PAT expires 2026-08-15`)*
