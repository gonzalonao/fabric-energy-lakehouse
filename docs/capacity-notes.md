# Capacity & cost notes (G3)

What this lakehouse actually costs to run, argued from live Fabric telemetry (run durations)
plus the known capacity SKU rather than guessed. The trial capacity is ephemeral (expires
~2026-07-31), so this file is the durable record of evidence that disappears with it.

Cross-references: build journal in
[`phases/track-a-progress.md`](phases/track-a-progress.md), the smoothing drills in
[`learning-log.md`](learning-log.md) (Phase G — Capacity & cost), decisions in
[`decisions.md`](decisions.md).

---

## Capacity under test

The project's workspaces run on a **Microsoft Fabric trial capacity**, which is **64 CU
(FTL64)** — the F64 compute equivalent — for every Fabric trial by definition. Trial capacities
are not billed and run a ~60-day window (this one expires ~2026-07-31). Region: West Europe
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
| `pl_backfill_ree` (prod) | manual, 2023-01 → 2026-07-23 | _TODO — read from `f6-backfill-prod-green.png`_ | one-off history load; 129 sequential chunks; wall-clock dominated by WAF-gated I/O (dev ran 3h53m49s) |
| `pl_daily_refresh` (prod) | manual (first prod run) | _TODO — read at F6 Step 3_ | the **recurring steady-state** cost; incremental ingest + full gold rebuild |
| `pl_daily_refresh` (dev, ref) | scheduled | ~3–5 min | dev daily runs (B8b: 3m42s / 5m16s) |

The recurring workload is **one daily refresh of a few minutes**, plus rare backfills. Light and
bursty — the ideal shape for a small capacity with 24h smoothing.

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

**Assessment:** this lakehouse runs comfortably on the **cheapest SKU, F2 (2 CU)**. A daily
refresh of a few minutes is a small fraction of an F2's daily CU-second budget, and PAYG F2 can
be **paused** between the daily window — a workload that runs minutes per day doesn't need a
capacity live 24/7. Honest production recommendation: **F2 pay-as-you-go with a pause schedule**,
stepping up only if interactive report concurrency or heavier transforms are added. The
F64-equivalent trial is ~32× larger than needed.

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

## TODO — capture before the trial expires (~2026-07-31)

- [ ] Fill the two duration cells above from the Monitor: `pl_backfill_ree` (from
      `f6-backfill-prod-green.png`) and the first prod `pl_daily_refresh` (F6 Step 3).
- [ ] Screenshot the prod `pl_daily_refresh` green run → `docs/evidence/phase-f/f6-daily-refresh-prod-green.png`.
- [ ] (Track B) With a self-administered capacity, connect the Metrics app and capture the
      itemized per-layer CU(s) — the breakdown this tenant can't provide.

## Sources

- [Microsoft Fabric Pricing 2026: F-SKU Costs & Licensing Guide (bminfotrade)](https://www.bminfotrade.com/blog/cloud-computing/microsoft-fabric-pricing-2026)
- [Microsoft Fabric Pricing 2026 — Synapx](https://www.synapx.com/blogs/microsoft-fabric-pricing-guide-2026/)
- [Microsoft Fabric Pricing 2026: Full F SKU Price List — Solv Systems](https://solv-systems.com/resources/microsoft-fabric-pricing-2026)
- Official (verify region): [Azure — Microsoft Fabric pricing](https://azure.microsoft.com/pricing/details/microsoft-fabric/)
