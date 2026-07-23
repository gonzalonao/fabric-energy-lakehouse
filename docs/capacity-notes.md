# Capacity & cost notes (G3)

What this lakehouse actually costs to run, measured on live Fabric telemetry rather than
guessed. Captured while the workload was under load so the numbers are real — the trial
capacity is ephemeral (expires ~2026-07-31), so this file is the durable record of evidence
that disappears with it.

Cross-references: build journal in
[`phases/track-a-progress.md`](phases/track-a-progress.md), the smoothing drills in
[`learning-log.md`](learning-log.md) (Phase G — Capacity & cost), decisions in
[`decisions.md`](decisions.md).

---

## Capacity under test

| Property | Value |
|---|---|
| SKU | **FTL64** — Fabric Trial License, **64 CU** (the F64 compute equivalent) |
| Type | Trial capacity (not billed; ~60-day window, expires ~2026-07-31) |
| Region | West Europe (student tenant) |
| Measured with | Microsoft Fabric Capacity Metrics app, connected as capacity admin |

The trial grants F64-equivalent compute. **This is what Microsoft hands out, not what the
workload needs** — see the cost model below, where the real requirement lands three SKU tiers
lower.

---

## The headline finding — a heavy backfill barely moves the needle

Running `pl_backfill_ree` in prod (2023-01 → 2026-07-23, ~4h, 129 sequential chunks) produced:

| Metric | Value |
|---|---|
| Avg utilization | **1.81 %** |
| Peak utilization | **1.82 %** |
| Total CU(s), all workspaces, 1-day | ~99,460 CU-seconds |
| Throttling (interactive delay / rejection / background rejection) | **none** |
| Overages | **none** |

A ~4-hour Spark-and-pipeline backfill showed as a **flat ~1.8% line**, not a spike. That is
**correct behaviour**, and understanding why is the whole point:

### Why it's flat — CU smoothing

Fabric bills compute in **CU-seconds** and *smooths* consumption before charging it against
the capacity:

- **Interactive** operations (e.g. report queries) smooth over a **5-minute** window.
- **Background** operations — **every data pipeline and Spark notebook run** — smooth over a
  **24-hour** window.

The backfill is entirely background work, so Fabric takes its total CU-seconds and **amortizes
them across 24 hours** instead of registering a burst. On 64 CU that amortized load lands at
~1.8%. The arithmetic is self-consistent: 1.81% × 64 CU × 86,400 s/day ≈ 99,460 CU(s), which
matches the metrics app's 1-day total — confirming the app is reading the right capacity.

Smoothing exists **by design**: it lets bursty batch work run on a small capacity without
tripping throttling, at the cost of making the utilization chart a poor proxy for "how much did
this job actually cost" — for that you read the **itemized CU(s)**, not the %.

### Why it's light in CU despite being long in wall-clock

The backfill is **network/latency-bound, not compute-bound**: 129 *sequential* HTTP fetches
behind REE's Imperva WAF (`Sequential = ON` is self-preservation, not politeness — see
decisions D5). Most of the ~4 hours is spent *waiting* on rate-limited I/O, which consumes
almost no CU. **Duration ≠ cost.**

---

## Cost model — what SKU this actually needs

Trial is FTL64/64 CU. The workload smoothed to <2% of that over a full day *including* other
tenant activity. The batch cadence (one daily refresh + occasional backfills) is light and
bursty — the ideal shape for a small capacity with smoothing.

**Reference F-SKU pricing** (US East, USD; regional variation exists but the SKU *ratios* are
constant — West Europe runs modestly higher):

| SKU | CU | Pay-as-you-go | Reserved (1-yr, ~41% less) |
|---|---:|---|---|
| **F2** | 2 | ~$0.36/hr (~$263/mo always-on) | ~$156/mo |
| **F4** | 4 | ~$526/mo always-on | ~$311/mo |
| **F64** | 64 | ~$8,410/mo always-on | ~$4,982/mo |

**Assessment:** this lakehouse would run comfortably on the **cheapest SKU, F2 (2 CU)**. A full
day's CU-seconds is a small fraction of an F2's daily budget at this cadence, and PAYG F2 can be
**paused** between the daily window — a batch workload that runs minutes per day doesn't need a
capacity live 24/7. The honest production recommendation is **F2 pay-as-you-go with a pause
schedule**, stepping up only if interactive report concurrency or heavier transforms are added.

The F64-equivalent trial is ~32× larger than needed — a useful reminder that trial size tells
you nothing about production sizing.

---

## Caveats on these numbers

- **Metrics-app ingestion lag.** Background operations report into the metrics dataset with
  delay, then smooth over 24h. At capture time the 1-day item table still attributed nearly all
  CU to a system **"Planning"** workspace and had **not** yet itemized `ws-energy-prod` /
  `pl_backfill_ree` / the Spark notebooks. The per-layer breakdown (which layer dominates cost —
  Spark vs pipeline) is therefore **TODO**, to be captured from the *settled* view after the
  backfill and first prod daily run complete.
- **Trial ≠ paid behaviour.** Trial capacities are not billed and do not enforce throttling the
  way a paid F-SKU does under sustained overage. "No throttling" here is expected and does not,
  on its own, prove the workload would never throttle a same-size paid capacity — though the
  <2% smoothed load makes that near-certain.
- **Pricing is US East, retrieved 2026-07-23.** Confirm West Europe rates against the live
  [Azure pricing calculator](https://azure.microsoft.com/pricing/details/microsoft-fabric/)
  before quoting a figure to a stakeholder.

---

## TODO — settle before the trial expires (~2026-07-31)

- [ ] Re-open the Capacity Metrics app **after** the backfill finishes and the first prod
      `pl_daily_refresh` runs; screenshot the **itemized 1-day CU(s) table** showing
      `ws-energy-prod` items → `docs/evidence/phase-f/g3-cu-breakdown-settled.png`. Record which
      layer (Spark notebooks vs pipeline vs SQL) is the top consumer and paste the CU(s) figures
      here.
- [ ] Capture the flat-ribbon Compute page (SKU FTL64 + avg/peak ~1.8%) →
      `g3-cu-smoothed.png`, and the empty Throttling/Overages tabs → `g3-no-throttling.png`.
- [ ] Note the **daily refresh** cost in isolation (one run's CU(s)) — the recurring steady-state
      number, distinct from the one-off backfill.

## Sources

- [Microsoft Fabric Pricing 2026: F-SKU Costs & Licensing Guide (bminfotrade)](https://www.bminfotrade.com/blog/cloud-computing/microsoft-fabric-pricing-2026)
- [Microsoft Fabric Pricing 2026 — Synapx](https://www.synapx.com/blogs/microsoft-fabric-pricing-guide-2026/)
- [Microsoft Fabric Pricing 2026: Full F SKU Price List — Solv Systems](https://solv-systems.com/resources/microsoft-fabric-pricing-2026)
- Official (verify region): [Azure — Microsoft Fabric pricing](https://azure.microsoft.com/pricing/details/microsoft-fabric/)
