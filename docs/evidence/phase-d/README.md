# Phase D — evidence

Screenshots proving the orchestration layer (`pl_daily_refresh`). Catalogued as captured.

## D1 — master pipeline `pl_daily_refresh`

| File | What it proves |
|---|---|
| `d1-alert-failure-proof.png` | **The failure path works end to end.** A controlled break (`nb_dq_gate_silver` run with `p_stage=silverX`, invalid → the gate raises before touching data) makes the run fail mid-chain. The Monitor run detail shows: ingest + all three silver notebooks **Succeeded**; `nb_dq_gate_silver` **Failed**; `nb_gold_build` and `nb_gold_mlv` **Skipped** (Gold never rebuilt from an ungated run); `alert_on_fail` **Succeeded** (exactly one email, sent to the `vl_energy` library variable address); `fail_run` **Failed**; and the pipeline overall reports **Failed**. This single run demonstrates all three guarantees — one alert on any failure, Gold protected by the gate, and an honest red status despite the alert succeeding (see the terminal-skip-funnel + Fail-activity design in [phase-d-orchestration.md](../../phases/phase-d-orchestration.md) Gotchas). |
| `d1-master-run-green.png` | **The clean end-to-end run.** Pipeline status **Succeeded**; the Output list shows all seven executed activities Succeeded — `inv_daily_ingest` (9m32s) → `nb_silver_demanda` → `nb_silver_generacion` → `nb_silver_precios` → `nb_dq_gate_silver` → `nb_gold_build` → `nb_gold_mlv` (~1m20s–1m52s each). `alert_on_fail` and `fail_run` are **absent from the list** — i.e. skipped — which is the success-path counterpart to the failure proof: the alert funnel stays silent when nothing breaks. |
| `d1-master-run-green-gantt.png` | **The chain really is sequential, not parallel.** Same green run in Monitor's **Gantt** view: each activity's bar starts only after the previous one ends (02:25 → 02:43). This is the visual proof of the D1 design decision — the three silver notebooks are chained one-after-another to avoid Spark session contention on the trial capacity, *not* because they'd collide in Delta (they write three different tables, so no `ConcurrentAppendException` is possible). |

## D2 — schedule moved to the master

| File | What it proves |
|---|---|
| `d2-master-schedule.png` | The daily 08:00 Europe/Madrid trigger now lives on `pl_daily_refresh`, with `pl_ingest_daily`'s own schedule disabled — so ingestion runs once per morning rather than twice (standalone + via the master's Invoke). Both changes serialize into Git as `.schedules` files. |

## D3 — scheduled proof

*(pending — two consecutive scheduled greens with **Run kind = Scheduled** visible. Note: "Submitted by" shows Gonzalo's name even for scheduled runs, so **Run kind** is the column that actually proves the schedule fired.)*
