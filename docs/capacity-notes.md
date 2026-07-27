# Capacity & cost notes (G3)

What this lakehouse actually costs to run, argued from live Fabric telemetry (run durations)
plus the known capacity SKU rather than guessed. The trial capacity is ephemeral (expires
~2026-08-05), so this file is the durable record of evidence that disappears with it.

Cross-references: the build narrative in [`build-log.md`](build-log.md), decisions in
[`decisions.md`](decisions.md).

---

## Capacity under test

The project's workspaces run on a **Microsoft Fabric trial capacity**, which is **64 CU
(FTL64)** — the F64 compute equivalent — for every Fabric trial by definition. Trial capacities
are not billed and run a ~60-day window (this one expires ~2026-08-05). Region: West Europe
(student tenant).

### Limitation — live per-item CU telemetry is unavailable on this tenant

The **Microsoft Fabric Capacity Metrics** app only surfaces capacities the signed-in user
*administers*. On this student tenant the only admin-visible capacity is an unrelated instance
(`Trial-20260601…`) hosting a single system `Planning` workspace — **not** `ws-energy-dev` or
`ws-energy-prod`. Over a 14-day window with all item kinds selected, **no project item appears**
(no `pl_*`, `nb_*`, or `ws-energy-*`), confirming the project's capacity is administered
elsewhere and its per-item CU breakdown can't be read here.

This parallels the **F1** SPN block: a student-tenant admin restriction, not a build gap. The
enterprise answer (a capacity the deploying identity administers, with the Metrics app connected
to it) is exactly what **Track B** — own tenant, Gonzalo as admin — will demonstrate. So the
cost model below is built from **Monitor run durations + the known 64-CU SKU**, which need no
capacity-admin rights.

---

## How Fabric charges compute — the model that makes the numbers make sense

Fabric bills compute in **CU-seconds** and *smooths* consumption before charging it:

- **Interactive** operations (e.g. report queries) smooth over a **5-minute** window.
- **Background** operations — **every data pipeline and Spark notebook run** — smooth over a
  **24-hour** window.

Consequence worth internalizing: a heavy-but-short **background** job (like a 4-hour backfill)
is **amortized across 24 hours**, so it never appears as a utilization *spike* — it shows as a
low sustained baseline. Smoothing exists by design, to let bursty batch work run on a small
capacity without tripping throttling. The corollary is that the utilization **%** is a poor
proxy for "what did this job cost"; for that you read the **itemized CU-seconds**.

A second reason our numbers are low: the backfill is **network/latency-bound, not
compute-bound** — 129 *sequential* HTTP fetches behind REE's Imperva WAF (`Sequential = ON`,
decisions D5). Most of its wall-clock is spent *waiting* on rate-limited I/O, which consumes
almost no CU. **Duration ≠ cost.**

---

## Observed cost evidence (from Monitor run durations)

| Run | Trigger | Duration | Notes |
|---|---|---|---|
| `pl_backfill_ree` (prod) | manual, 2023-01 → 2026-07-23 | **3h09m** | one-off history load; 129 sequential chunks; wall-clock dominated by WAF-gated I/O (dev ran 3h53m49s) |
| `pl_daily_refresh` (prod) | manual, first prod run | **18 min** | full medallion chain: incremental ingest → 3× silver → DQ gate → full gold rebuild → MLV refresh |
| `pl_daily_refresh` (prod) | **scheduled, 08:00** (unattended) | **24 min** | the **recurring steady-state** cost — see the scheduled-run finding below |
| `pl_ingest_daily` (dev, ref) | scheduled | ~3–5 min | ingest leg only (B8b: 3m42s / 5m16s), not the full chain |

The recurring workload is **one ~20-minute background run per day**, plus rare backfills. Light
and bursty — the ideal shape for a small capacity with 24h smoothing.

### Where the time goes — per-activity breakdown

From the 18m09s manual prod run (`f6-daily-refresh-prod-chain.png`, activity-runs list):

| Activity | Duration | Layer |
|---|---:|---|
| `inv_daily_ingest` | 7m42s | ingest (network-bound) |
| `nb_silver_demanda` | 1m22s | silver |
| `nb_silver_generacion` | 1m37s | silver |
| `nb_silver_precios` | 1m22s | silver |
| `nb_dq_gate_silver` | 2m09s | DQ gate |
| `nb_gold_build` | 1m54s | gold |
| `nb_gold_mlv` | 1m38s | gold (MLV refresh) |
| **Sum of activities** | **17m44s** | (balance = orchestration overhead) |

**Ingest is ~43 % of wall-clock but close to 0 % of CU** — it's HTTP waiting, not compute. The
six Spark activities are ~57 % of the time and essentially *all* of the CU. This is a duration
proxy, not a CU measurement (see the telemetry limitation above), but it's directionally
sufficient: **the Spark layer is the cost driver, and the DQ gate + gold rebuild are the two
biggest Spark consumers.** If this workload ever needed tuning for cost, `nb_dq_gate_silver`
and `nb_gold_build` are where to look — not the ingest that dominates the clock.

### The schedule deployed itself

The prod 08:00 run was **never configured by hand**. Fabric serializes a pipeline's schedule
into Git as a dedicated `.schedules` file (B9, commit `f233aef` — its own JSON schema, carrying
`localTimeZoneId: Romance Standard Time`), so `fabric-cicd` published it as part of the item
definition and **prod inherited an active daily trigger from `main`**. Prod is therefore not
merely a deployed copy but a **self-operating environment** — deployment reproduced the
*operational* behaviour, not just the item graph. This is the strongest single piece of F7
evidence: it is only possible because prod was built from source control rather than clicked
together.

⚠️ **Operational consequence:** prod now consumes capacity every morning at 08:00 unattended,
and will keep firing until the trial capacity expires (~2026-08-05), after which the runs fail
rather than stopping quietly. Disable the prod schedule if the noise matters before then.

### Why prod's ~20 min vs dev's few minutes

Not a regression, and not a prod-vs-dev difference in efficiency. The dev reference figure is
`pl_ingest_daily` — the **ingest leg alone**. Prod's number is the **full master chain**, whose
dominant costs are a cold Spark session start against the custom `env_energy` environment
(custom-library startup is minutes, paid once per run) and the **full atomic gold rebuild**
over all three years of history (decisions D10 — gold is rebuilt from scratch each run, not
merged). Both are by design; the 18→24 min spread between two runs of the same pipeline is
normal Spark session-acquisition variance.

---

## Cost model — what SKU this actually needs

Trial is 64 CU. The recurring workload is minutes of background compute per day. Sizing off the
*trial* is meaningless — the trial is what Microsoft grants, not what the workload needs.

**Reference F-SKU pricing** (US East, USD, retrieved 2026-07-23; regional variation exists but
SKU *ratios* are constant — West Europe runs modestly higher):

| SKU | CU | Pay-as-you-go | Reserved (1-yr, ~41% less) |
|---|---:|---|---|
| **F2** | 2 | ~$0.36/hr (~$263/mo always-on) | ~$156/mo |
| **F4** | 4 | ~$526/mo always-on | ~$311/mo |
| **F64** | 64 | ~$8,410/mo always-on | ~$4,982/mo |

**Assessment: this lakehouse runs comfortably on the cheapest SKU, F2 (2 CU).** Sizing argument
from the measured 24-minute daily run:

- Fabric bills Spark at **1 CU = 2 Spark vCores**. A small default pool allocating ~8 vCores
  ⇒ ~4 CU while active.
- 4 CU × 1,440 s (24 min) ≈ **5,800 CU-seconds per day**.
- An **F2** provides 2 CU × 86,400 s = **172,800 CU-seconds/day**.
- The daily refresh therefore consumes roughly **3–4 % of an F2's daily budget** — and 24-hour
  background smoothing spreads even that across the day, so the burst never approaches the
  ceiling.

*(vCore allocation is an assumption — the exact figure needs the per-item CU breakdown this
tenant can't provide. Even at 4× the estimate the conclusion holds.)*

Honest production recommendation: **F2 pay-as-you-go**, optionally paused outside the daily
window. One nuance if pausing: accumulated smoothed background charges are billed as a lump at
pause time, so pausing shifts *when* you pay rather than avoiding the CU-seconds already
consumed — the saving comes from not renting idle capacity, which for a minutes-per-day workload
is still most of the bill. Step up to F4+ only if interactive report concurrency or heavier
transforms are added.

The F64-equivalent trial is ~32× larger than this workload needs — a useful reminder that trial
size tells you nothing about production sizing.

---

## Caveats

- **Per-item CU breakdown unavailable** on this tenant (see the limitation above). The
  which-layer-dominates-cost question (Spark vs pipeline vs SQL) is answerable on **Track B**,
  where the capacity is self-administered.
- **Trial ≠ paid behaviour.** Trial capacities aren't billed and don't enforce throttling the
  way a paid F-SKU does under sustained overage. The workload's minutes-per-day cadence makes
  throttling a non-issue on any SKU here regardless.
- **Pricing is US East, retrieved 2026-07-23.** Confirm West Europe against the live
  [Azure pricing calculator](https://azure.microsoft.com/pricing/details/microsoft-fabric/)
  before quoting a figure to a stakeholder.

---

## TODO — capture before the trial expires (~2026-08-05)

- [x] Durations captured from the Monitor (backfill 3h09m; prod daily 18 min manual / 24 min
      scheduled) — 2026-07-24.
- [ ] Screenshot the prod `pl_daily_refresh` green runs → `docs/evidence/phase-f/f6-daily-refresh-prod-green.png`.
      **Capture the scheduled 08:00 one with the `Run kind = Scheduled` column visible** — that
      is the self-operating-prod proof.
- [ ] Decide whether to disable the prod 08:00 schedule before the trial lapses (~2026-08-05).
- [ ] (Track B) With a self-administered capacity, connect the Metrics app and capture the
      itemized per-layer CU(s) — the breakdown this tenant can't provide.

## Sources

- [Microsoft Fabric Pricing 2026: F-SKU Costs & Licensing Guide (bminfotrade)](https://www.bminfotrade.com/blog/cloud-computing/microsoft-fabric-pricing-2026)
- [Microsoft Fabric Pricing 2026 — Synapx](https://www.synapx.com/blogs/microsoft-fabric-pricing-guide-2026/)
- [Microsoft Fabric Pricing 2026: Full F SKU Price List — Solv Systems](https://solv-systems.com/resources/microsoft-fabric-pricing-2026)
- Official (verify region): [Azure — Microsoft Fabric pricing](https://azure.microsoft.com/pricing/details/microsoft-fabric/)
