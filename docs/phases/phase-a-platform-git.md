# Phase A — Platform & Git

**Status:** 🔄 in progress (at step A4, Track A)
**Days:** D1 (≈ 2026-07-11) · **Plan:** [P1 §Phase A](../fabric-p1-energy-lakehouse.md) ·
**Tracks:** [tracks.md](tracks.md) (A = Azure DevOps, active · B = GitHub, planned)

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
| Git provider | **Track A: Azure DevOps** (GitHub provider blocked on the student tenant) with GitHub kept canonical via mirroring · **Track B: GitHub** fine-grained PAT scoped to this repo | See `tracks.md`; two-track decision 2026-07-13 |
| Semantic model storage format | **Large** (workspace Advanced setting) | Direct Lake (Phase E) requires the large format; no downside at our scale — model lives as TMDL in Git, not .pbix |

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

### A4 `[YOU]` Git provider setup

**`[Track A — Azure DevOps]`** *(active)*

- [ ] Go to `https://dev.azure.com` and sign in with the **student account** (same
      identity you use in Fabric — the DevOps org must live in the same tenant for
      user-auth Git integration).
- [ ] Create the organization when prompted (**New organization / Get started**):
      name e.g. `gonzalonao-fabric` (globally unique), region **West Europe**.
      🚩 If org creation errors with an admin-restriction message, the tenant blocks
      DevOps orgs too — stop and log it (accelerates Track B instead).
- [ ] Create project `fabric-energy-lakehouse` — visibility **Private**, version
      control **Git**.
- [ ] **Repos → Import repository** → Clone URL
      `https://github.com/gonzalonao/fabric-energy-lakehouse.git` (public, no auth) →
      Import. Verify branches `develop` and `main` arrived with full history.
- [ ] **Repos → Branches** → set **`develop` as the default branch** (⋯ menu).

**`[Track B — GitHub]`** *(own tenant)*

- [ ] GitHub → **Settings → Developer settings → Fine-grained tokens → Generate new
      token**.
- [ ] Name `fabric-git-integration`; expiration past the capacity window.
- [ ] Repository access: **Only select repositories** → `gonzalonao/fabric-energy-lakehouse`.
- [ ] Permissions → Repository permissions → **Contents: Read and write**
      (Metadata: Read is added automatically).
- [ ] Generate and copy the token. It goes **nowhere near this repo** — paste it only
      into the Fabric connection dialog in A5 (keep it in your password manager until then).

### A5 `[YOU]` Bind `ws-energy-dev` ↔ `develop`

- [ ] `ws-energy-dev` → **Workspace settings** → **Git integration**.
- [ ] **`[Track A]`** Provider: **Azure DevOps** → account is detected from your signed-in
      identity → pick Organization `gonzalonao-fabric` · Project
      `fabric-energy-lakehouse` · Repository `fabric-energy-lakehouse`.
      **`[Track B]`** Provider: **GitHub** → **Add account** → paste the PAT from A4 →
      connect → Repository `gonzalonao/fabric-energy-lakehouse`.
- [ ] Branch: **`develop`** · Git folder: **`/fabric`** (both tracks).
- [ ] **Connect and sync.** The repo has no `/fabric` folder yet, so Fabric will offer
      to commit the workspace content into the branch — accept (direction:
      workspace → Git).
- [ ] Verify: the workspace header shows the branch name / **Source control** button
      with `0` pending changes.

### A6 `[CLAUDE]` Verify the sync landed in the repo

- [ ] **`[Track A]`** Add the DevOps remote locally (`git remote add devops <url>`;
      auth via Git Credential Manager browser login on first fetch), pull
      `devops/develop`, **push to `origin`** — the GitHub mirror now carries the Fabric
      commit. **`[Track B]`** plain `git pull` on `develop`.
- [ ] Confirm `fabric/lh_energy.Lakehouse/` exists (a `.platform` metadata file — item
      definitions only, never data).
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
      comment line and change `SELECT 1` to `SELECT 2`); push; open a PR into `develop`
      **on GitHub** (both tracks — GitHub is canonical for review).
- [ ] Verify the PR diff renders as a clean line-level Python diff (screenshot-worthy —
      this is the "notebooks are reviewable" portfolio claim). Merge the PR.
- [ ] **`[Track A]`** After the merge, push `develop` to the `devops` remote so Fabric
      can see it (mirror rule: GitHub → DevOps before any *Update all*).

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

- 2026-07-13 — **A5 blocked: GitHub Git provider disabled on the tenant.** In Git
  integration the GitHub option is greyed out ("Contact an admin to allow this git
  provider"); only Azure DevOps is available. The account is a student account on the
  institution's (ESESA/UCAM) tenant — no tenant admin, Admin portal shows no Tenant
  settings.
- 2026-07-13 — **"Create own tenant + free Fabric trial" researched and ruled out.**
  As of late 2025/2026, Microsoft blocks Fabric trial activation on newly created
  Entra/M365 tenants (anti-abuse policy; ~90-day cooling-off; one trial per user
  identity GUID, no self-service reset). New trials also default to F4, not F64.
  Viable alternatives identified: (a) stay on student tenant + **Azure DevOps** Git
  integration (available) with a GitHub mirror for portfolio evidence; (b) own tenant +
  **paid F2** funded by the Azure free $200/30-day credit (Microsoft-documented; pause
  when idle; auto-disables at credit end so no charge risk; caveats: 30-day window,
  Power BI Pro licensing on a fresh tenant unverified); (c) ask institution IT to
  enable the GitHub provider (email drafted, sent by Gonzalo). Decision pending.

## Session log

- 2026-07-10 — Repo prep before D1: added portfolio/learning/doc standing objectives to
  CLAUDE.md, wove 📣/🎓 checkpoints into all phase guides, added C–G guides. Phase A
  opened; A1–A5 are Gonzalo's next (Fabric portal). Nothing built in Fabric yet.
- 2026-07-13 — A1–A3 worked through on the student tenant (workspaces on Large semantic
  model format, template apps off — checkboxes to be ticked once confirmed); A5 blocked
  at the GitHub provider (see Gotchas). Deep-dived tenant/trial options; three candidate
  paths documented, IT email drafted. Phase paused at A5 pending path decision.
- 2026-07-13 (later) — **Decision: two-track execution** (see `tracks.md` + CLAUDE.md
  mirror rule): Track A = Azure DevOps on the student tenant now, Track B = GitHub on an
  own tenant + credit-funded F2 later. Phase A steps A4–A6/A8 rewritten as track
  variants; resuming at A4 `[Track A]` (create the DevOps org). IT email to enable
  GitHub still worth sending — if granted, Track A can swap provider cheaply.
