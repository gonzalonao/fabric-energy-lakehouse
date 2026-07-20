# Phase D — evidence

Screenshots proving the orchestration layer (`pl_daily_refresh`). Catalogued as captured.

## D1 — master pipeline `pl_daily_refresh`

| File | What it proves |
|---|---|
| `d1-alert-failure-proof.png` | **The failure path works end to end.** A controlled break (`nb_dq_gate_silver` run with `p_stage=silverX`, invalid → the gate raises before touching data) makes the run fail mid-chain. The Monitor run detail shows: ingest + all three silver notebooks **Succeeded**; `nb_dq_gate_silver` **Failed**; `nb_gold_build` and `nb_gold_mlv` **Skipped** (Gold never rebuilt from an ungated run); `alert_on_fail` **Succeeded** (exactly one email, sent to the `vl_energy` library variable address); `fail_run` **Failed**; and the pipeline overall reports **Failed**. This single run demonstrates all three guarantees — one alert on any failure, Gold protected by the gate, and an honest red status despite the alert succeeding (see the terminal-skip-funnel + Fail-activity design in [phase-d-orchestration.md](../../phases/phase-d-orchestration.md) Gotchas). |
| `d1-master-run-green.png` | *(pending)* The clean end-to-end run: every stage **Succeeded** in order, `alert_on_fail` and `fail_run` both **Skipped**. |

## D3 — scheduled proof

*(pending — two consecutive scheduled greens with **Run kind = Scheduled** visible.)*
