# Phase C — evidence

Screenshots proving the Transform & data-quality milestone (Track A). Earlier phases:
[phase-a/](../phase-a/README.md) · [phase-b/](../phase-b/README.md).

| File | What it proves |
|---|---|
| `c3-env-published.png` | The **typed-helpers-as-a-wheel** claim made real: the `env_energy` environment's **Custom libraries** pane lists `energy_lakehouse-0.1.0-py3-none-any.whl` with **Status = Success** (published), on **Runtime 1.3 (Spark 3.5, Delta 3.2)**. This is the artifact C2 built, now installed on the cluster — the notebooks in C4 just `import energy_lakehouse`. Runtime 1.3 also pins the Python version (3.11), which is exactly what the package targets |
| `c3-spark-default.png` | The environment is the **workspace Spark default**: Workspace settings → Data Engineering/Science → Spark settings → **Environment** tab → *Set default environment = On*, `env_energy` selected. So every notebook starts with the wheel available without per-notebook attachment — the mechanism that lets the thin C4 notebooks import the package with zero setup |
| `c4-dq-gate-green.png` | The **DQ gate passing on real data after a real fix**: `nb_dq_gate`'s gate cell green (`INFO … DQ gate passed for stage='silver'`, 1m24s, wheel 0.2.0) above an `ops.dq_results` query of the latest `run_ts` — **20 rows, and the status column's profile panel reads `Unique: 1`**, i.e. every check PASS, provable from the frame itself. The rows enumerate the whole check surface per table (freshness, null_pct per key column, row_count, row_count_delta, value_range). Read against the C4 Gotcha: the previous run **failed** on 8 negative `Carbón` rows — this green is the renewable-aware bound shipped as 0.2.0, not a loosened gate |
| `c4-silver-tables.png` | Silver is **built and schema-namespaced**: Explorer → `lh_energy` → Tables shows `dbo`, `bronze`, and **`silver`** (with `demand_daily`, `generation_daily`, `price_hourly`), plus `Files/raw`. The `demand_daily` preview shows typed `date`/`value` rows in the 576k–823k MWh band (units confirmed → MWh). No `quarantine` table appears — correct, because the clean backfill produced zero structural parse failures (quarantine is created only when something lands in it) |

**Notes**

- Read as a pair, these two shots are the C3 story: the wheel is **published** (`c3-env-published`)
  and **wired in as the default** (`c3-spark-default`). Together they back the portfolio line
  "typed, tested helper package on a Fabric Environment; notebooks stay thin."
- The money shots for Phase C come later: the **corrupted-file DQ failure** (C5) and the **SQL
  analytics endpoint proofs** (C7).
