# Phase F — evidence

Screenshots proving the CI/CD layer: `develop` → `main` → **prod**, deployed by
`scripts/deploy.py` (`fabric-cicd`) and never hand-edited. Catalogued as captured.

Context that shapes what could be captured: the student tenant **blocks service-principal
registration** (F1, Entra admin centre 401), so prod deploys run the same script locally with
interactive auth — same code, same commit, different identity and trigger. The tenant also
hides the project's capacity from the Capacity Metrics app, so cost evidence is
duration-based (see [`capacity-notes.md`](../../capacity-notes.md)).

## F6 — deploy to prod + the prod data load

| File | What it proves |
|---|---|
| `f6-backfill-prod-green.png` | **Prod loaded its own history.** `pl_backfill_ree` **Succeeded** in `ws-energy-prod`, `2023-01-01 → 2026-07-23`, **3h09m**, 129 sequential chunks. Prod's lakehouse is populated by *running the deployed pipelines*, not by copying dev's data — the two environments share definitions, never storage. |
| `f6-daily-refresh-prod-chain.png` | **The whole medallion chain runs in prod.** Monitor run detail for the first manual `pl_daily_refresh` (7/24/2026 21:14:48 → 21:32:57, **18m09s**, **Succeeded**). The graph shows the deployed dependency chain intact — `inv_daily_ingest` → `nb_silver_demanda` → `nb_silver_generacion` → `nb_silver_precios` → `nb_dq_gate_silver` → `nb_gold_build` → `nb_gold_mlv` — and the Activity runs list shows all **7 Succeeded** with per-activity durations. `alert_on_fail` and `fail_run` are absent (skipped), the success-path counterpart to D1's failure proof. The durations are the source of the per-layer cost breakdown in `capacity-notes.md`: ingest is 43% of the clock but ~0% of the CU. |
| `f6-daily-refresh-prod-scheduled.png` | **Prod is self-operating.** `pl_daily_refresh` · **Succeeded** · `07/25/2026, 8:00 AM` · **Run kind = Scheduled**. Nobody configured this trigger in prod: Fabric serializes a pipeline's schedule into Git as a `.schedules` file (B9, `f233aef`), so `fabric-cicd` published the **active daily schedule** as part of the item definition. Deployment reproduced the *operational behaviour*, not just the item graph — only possible because prod was built from source control instead of clicked together. **`Run kind` is the load-bearing column**: *Submitted by* shows Gonzalo's name even on scheduled runs. |

## F7 — prod verified untouched-by-hand

| File | What it proves |
|---|---|
| `f7-model-prod-binding.png` | **A real deployment defect, caught and fixed.** `sm_energy`'s prod data source now reads `onelake.dfs.fabric.microsoft.com/`**`30ace2e2-…888722`**`/`**`dab61d02-…486fe`** — prod's workspace and prod's *own* lakehouse (a GUID that exists nowhere in dev), with `Last refresh succeeded`. Before the fix it read `476b58fd-…/6cabfc1b-…` — **dev's** workspace and lakehouse — because Direct Lake **on OneLake** stores its source as a Power Query M expression (`definition/expressions.tmdl`) that `fabric-cicd`'s same-workspace auto-re-point cannot reach into, and `parameter.yml` scoped both GUID substitutions to `item_type: "Notebook"`. Prod's report was rendering **dev's data while looking perfectly healthy** — M3's silent-wrong-target failure in the one item type where nothing throws. Fixed by broadening both entries to `["Notebook", "SemanticModel"]` (`8bfc057`). |
| `f7-report-prod-rendered.png` | **Prod serves prod data, with no fallback path.** `rpt_energy` open on the Demand page, all three pages present, rendering 2023-01 → 2026-06 of prod's own gold tables. On **Direct Lake on OneLake** there is no DirectQuery fallback (decisions D13), so a rendered page is the no-fallback proof by construction. It also validates two Phase E model-layer fixes in prod: the trend stops at **June 2026** (July excluded as a partial month by `Total Demand (Complete Months)`) and **Demand YoY % (R12) = 2.4%**, a defensible figure where the old unguarded measure read a meaningless 40.5%. |

### A note on what these two screenshots together establish

`f7-report-prod-rendered.png` alone cannot prove the report reads *prod's* lakehouse — the
defective build rendered just as beautifully against dev. The workspace binding in
`f7-model-prod-binding.png` is what closes that gap, and the report binds to the model by
relative path (`byPath: ../sm_energy.SemanticModel`), so the two shots chain.

**The general lesson, worth more than either screenshot:** every F7 check that passed —
16/16 items present, notebook bindings correct, pipeline sink correct, report renders — is a
check that can only fail *loudly*. None of them could detect a wrong-but-valid target. The
only test that catches a silent misbinding is reading the binding itself.
