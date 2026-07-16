# Phase B — evidence

Screenshots proving the Batch ingestion milestone (Track A). Phase A's evidence:
[phase-a/](../phase-a/README.md).

| File | What it proves |
|---|---|
| `b2-pending-commit.png` | Fabric **holding an uncommitted change**: Source control panel on branch `develop`, `Changes 1`, `vl_energy` flagged **Added** (green `+`), commit message box still empty. Git sync is a **deliberate action**, not a file watcher — the workspace and the branch are legitimately out of step until a human clicks *Commit* |
| `b3-bronze-json-raw.png` | Bronze is **byte-faithful**: the landed file opens as REE's own JSON:API envelope (`{"data":{"type":"Evolución de la demanda","id":"dem1","attributes":{…`) on a single line — not flattened, not JSON-Lines, not reshaped. Achieved by leaving the Copy activity's **Mapping tab empty** (default schema mapping = response written as-is). Independently corroborated: the raw API response is 2946 bytes and the landed file reads 2 KB |
| `b3-run1-file-landed.png` | The parameterized path resolved correctly: `Files/raw/demanda_evolucion/2024/01/demanda_evolucion_202401.json`, **1 item**, modified **2:39:22 PM**. Folder and file name are derived from `p_start` alone |
| `b3-run2-idempotent-rerun.png` | **Idempotency at the unit level** — the same run repeated with identical parameters: still **1 item**, same name, no `_1` suffix, modified now **2:42:54 PM**. It re-wrote rather than duplicating or skipping. Note what is *absent* from this proof: no watermark was consulted (`pl_ingest_ree` has none) — idempotency comes from the deterministic path + overwrite, which is why the B8 kill-test works |
| `b4-update-all-pending.png` | The **other direction** of the manual sync: Source control → *Updates* tab, **2** incoming changes (`nb_gen_backfill_chunks`, `nb_update_watermark`) waiting for *Update all*. Read as a pair with `b2-pending-commit.png` (outgoing), these show both halves of Git integration being deliberate — Fabric never moves code either way on its own |
| `b4-ctl-watermark-bronze-schema.png` | Two things at once. (1) **The schema-enabled lakehouse works**: `Tables` contains `dbo` *and* `bronze` as schema nodes (schema icon, not folder icon), with `ctl_watermark` nested under `bronze` — the payoff of A3's irreversible checkbox and the prerequisite for Phase C's materialized lake views. (2) **The watermark bootstrapped correctly**: one row, `demanda_evolucion` / `2022-12-31T23:59`, `updated_at` = `2026-07-16T18:04:41.000Z` — stored in **UTC**, so the control table never participates in the DST problem the REE payloads have |

**Notes**

- `b2-pending-commit.png` is the shot that was missed at A7 (the pending state had already
  been committed by the time we looked). It is the visual counterpart to Phase A's
  `a2-folders-lakehouse.png`, which shows the *Synced* state — together they show both
  sides of the manual-sync boundary.
- `b3-run1-*` and `b3-run2-*` are a **pair** and only mean anything read together: the point
  is that the file **count** didn't change while the **timestamp** did.
- `b2-pending-commit.png` (outgoing) and `b4-update-all-pending.png` (incoming) are likewise a
  pair — the two directions of a sync that is manual in both.
