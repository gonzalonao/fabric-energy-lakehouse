# Phase B — evidence

Screenshots proving the Batch ingestion milestone (Track A). Phase A's evidence:
[phase-a/](../phase-a/README.md).

| File | What it proves |
|---|---|
| `b2-pending-commit.png` | Fabric **holding an uncommitted change**: Source control panel on branch `develop`, `Changes 1`, `vl_energy` flagged **Added** (green `+`), commit message box still empty. Git sync is a **deliberate action**, not a file watcher — the workspace and the branch are legitimately out of step until a human clicks *Commit* |
| `b3-bronze-json-raw.png` | Bronze is **byte-faithful**: the landed file opens as REE's own JSON:API envelope (`{"data":{"type":"Evolución de la demanda","id":"dem1","attributes":{…`) on a single line — not flattened, not JSON-Lines, not reshaped. Achieved by leaving the Copy activity's **Mapping tab empty** (default schema mapping = response written as-is). Independently corroborated: the raw API response is 2946 bytes and the landed file reads 2 KB |
| `b3-run1-file-landed.png` | The parameterized path resolved correctly: `Files/raw/demanda_evolucion/2024/01/demanda_evolucion_202401.json`, **1 item**, modified **2:39:22 PM**. Folder and file name are derived from `p_start` alone |
| `b3-run2-idempotent-rerun.png` | **Idempotency at the unit level** — the same run repeated with identical parameters: still **1 item**, same name, no `_1` suffix, modified now **2:42:54 PM**. It re-wrote rather than duplicating or skipping. Note what is *absent* from this proof: no watermark was consulted (`pl_ingest_ree` has none) — idempotency comes from the deterministic path + overwrite, which is why the B8 kill-test works |

**Notes**

- `b2-pending-commit.png` is the shot that was missed at A7 (the pending state had already
  been committed by the time we looked). It is the visual counterpart to Phase A's
  `a2-folders-lakehouse.png`, which shows the *Synced* state — together they show both
  sides of the manual-sync boundary.
- `b3-run1-*` and `b3-run2-*` are a **pair** and only mean anything read together: the point
  is that the file **count** didn't change while the **timestamp** did.
