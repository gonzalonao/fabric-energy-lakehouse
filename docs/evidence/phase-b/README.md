# Phase B — evidence

Screenshots proving the Batch ingestion milestone (Track A). Phase A's evidence:
[phase-a/](../phase-a/README.md).

| File | What it proves |
|---|---|
| `b2-pending-commit.png` | Fabric **holding an uncommitted change**: Source control panel on branch `develop`, `Changes 1`, `vl_energy` flagged **Added** (green `+`), commit message box still empty. Git sync is a **deliberate action**, not a file watcher — the workspace and the branch are legitimately out of step until a human clicks *Commit* |

**Notes**

- `b2-pending-commit.png` is the shot that was missed at A7 (the pending state had already
  been committed by the time we looked). It is the visual counterpart to Phase A's
  `a2-folders-lakehouse.png`, which shows the *Synced* state — together they show both
  sides of the manual-sync boundary.
