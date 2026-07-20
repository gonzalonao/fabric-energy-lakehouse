# Phase C — evidence

Screenshots proving the Transform & data-quality milestone (Track A). Earlier phases:
[phase-a/](../phase-a/README.md) · [phase-b/](../phase-b/README.md).

| File | What it proves |
|---|---|
| `c3-env-published.png` | The **typed-helpers-as-a-wheel** claim made real: the `env_energy` environment's **Custom libraries** pane lists `energy_lakehouse-0.1.0-py3-none-any.whl` with **Status = Success** (published), on **Runtime 1.3 (Spark 3.5, Delta 3.2)**. This is the artifact C2 built, now installed on the cluster — the notebooks in C4 just `import energy_lakehouse`. Runtime 1.3 also pins the Python version (3.11), which is exactly what the package targets |
| `c3-spark-default.png` | The environment is the **workspace Spark default**: Workspace settings → Data Engineering/Science → Spark settings → **Environment** tab → *Set default environment = On*, `env_energy` selected. So every notebook starts with the wheel available without per-notebook attachment — the mechanism that lets the thin C4 notebooks import the package with zero setup |
| `c4-dq-gate-green.png` | The **DQ gate passing on real data after a real fix**: `nb_dq_gate`'s gate cell green (`INFO … DQ gate passed for stage='silver'`, 1m24s, wheel 0.2.0) above an `ops.dq_results` query of the latest `run_ts` — **20 rows, and the status column's profile panel reads `Unique: 1`**, i.e. every check PASS, provable from the frame itself. The rows enumerate the whole check surface per table (freshness, null_pct per key column, row_count, row_count_delta, value_range). Read against the C4 Gotcha: the previous run **failed** on 8 negative `Carbón` rows — this green is the renewable-aware bound shipped as 0.2.0, not a loosened gate |
| `c4-silver-tables.png` | Silver is **built and schema-namespaced**: Explorer → `lh_energy` → Tables shows `dbo`, `bronze`, and **`silver`** (with `demand_daily`, `generation_daily`, `price_hourly`), plus `Files/raw`. The `demand_daily` preview shows typed `date`/`value` rows in the 576k–823k MWh band (units confirmed → MWh). No `quarantine` table appears — correct, because the clean backfill produced zero structural parse failures (quarantine is created only when something lands in it) |

| `c5-quarantine-rows.png` | **Structural failures quarantine without failing the run**: after the corrupt Bronze file landed, `nb_bronze_to_silver` finishes green with `1267 rows, 2 quarantined` (1264 good rows from the other 42 files + the 3 negatives that *parse* fine), and `silver.quarantine` holds exactly 2 rows with machine-readable reasons (`non-numeric value None`, `'datetime'`) plus the offending raw JSON. The structural/semantic boundary made visible: what can't become a typed row is preserved for audit; what can, proceeds — to be judged by the gate |
| `c5-dq-gate-fail.png` | **Money shot #1 — the gate kills the run on semantic corruption**: red `DQGateError: DQ gate failed (1 check(s)): silver.demand_daily.value value_range: 3 rows outside [0.0, inf]` — rule, table, column and count all in the message. Below it, `ops.dq_results` already contains the `FAIL` row (`value_range` / `silver.demand_daily` / observed `3.0`) — written **before** the raise, so the failure is diagnosable from a query, not just stderr. In a pipeline this exception is what stops Gold from consuming poisoned Silver |
| `c5-gate-green-restored.png` | **Recovery without cleanup logic**: one `pl_ingest_ree` re-run (Jan 2024 window) overwrote the corrupt month file — the deterministic path + whole-file overwrite is the recovery mechanism, same property the B8c kill-test proved — then the silver MERGE healed the 3 poisoned dates (grid shows `2024-01-05/06/07` back at real values 697927/614433/637873 MWh) and the gate returned `DQ gate passed for stage='silver'`. The quarantine rows stay behind as a permanent audit trail (append-only, by design) |

| `c6-gold-tables.png` | The **full medallion in one Explorer frame**: `Tables` holds schema nodes `dbo`, `bronze`, `gold`, `ops`, `silver` — with `gold` expanded to its 8 objects: 3 dims (`dim_date`, `dim_indicator`, `dim_technology`), 3 facts (`fact_demand_daily`, `fact_generation_daily`, `fact_price_hourly`), and the 2 **materialized lake views** (`mlv_monthly_avg_price`, `mlv_monthly_renewables_share`, distinct MLV icon). The MLVs are the payoff of A3's irreversible schemas checkbox — they require a schema-enabled lakehouse. Counts verified on build: dim_date 1826 / dim_technology 15 / dim_indicator 3 / facts 1295 · 19412 · 102763 |

**Notes**

- Read as a pair, these two shots are the C3 story: the wheel is **published** (`c3-env-published`)
  and **wired in as the default** (`c3-spark-default`). Together they back the portfolio line
  "typed, tested helper package on a Fabric Environment; notebooks stay thin."
- The three `c5-*` shots are one story in sequence — quarantine (run survives) → gate FAIL
  (run dies, on purpose) → restore (green with zero cleanup code). Read with the phase guide's
  C5 Gotcha: the same test also exposed and fixed a real reader bug (`wholetext` silently
  clobbered by `text()`'s keyword default — latent while every JsonSink file was single-line).
- Remaining money shot for Phase C: the **SQL analytics endpoint proofs** (C7).
