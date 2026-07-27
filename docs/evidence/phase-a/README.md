# Phase A — evidence

Screenshots proving the Platform & Git milestone (Track A — Azure DevOps as the Fabric
Git provider, with **GitHub kept canonical** via mirroring — see
the build log).

| File | What it proves |
|---|---|
| `a1-workspaces.png` | `ws-energy-dev` and `ws-energy-prod` both exist on trial capacity |
| `a2-folders-lakehouse.png` | Workspace layout: folders `bronze/silver/gold/orchestration` + `lh_energy` at root, **Git status: Synced** |
| `a3-lakehouse-schemas.png` | Lakehouse Tables tree shows the `dbo` schema node — **schema-enabled lakehouse** (irreversible setting; required by the Phase C materialized lake views) |
| `a5-git-integration.png` | Fabric Git integration connected: provider **Azure DevOps**, org `glopezc443`, repo `fabric-energy-lakehouse`, folder `/fabric`, branch `develop` |
| `a8-pr-diff.png` | **The headline artifact** — [PR #1](https://github.com/gonzalonao/fabric-energy-lakehouse/pull/1) rendering the notebook as a clean line-level Python diff (`SELECT 1` → `SELECT 2` + comment). Fabric notebooks are stored as `.py`, so they are reviewable in a PR — unlike opaque `.ipynb`/`.pbix` binaries |
| `a9-notebook-select2.png` | The repo edit pulled **back into** the Fabric workspace via *Source control → Update all* — closing the bidirectional round-trip |

Together `a8` + `a9` demonstrate Git integration in **both directions**: Fabric → repo
(commit from the workspace, A7) and repo → Fabric (PR merged, then Update all, A9).

**Notes**
- The Entra account email in `a5` is redacted — it carries no evidential value and this
  repo is public.
- The A7 "mid-commit" Source control panel was not captured (the pending-change state had
  already been committed); the commit itself is evidenced by `826232f` in the history and
  by the Synced status in `a2`.
