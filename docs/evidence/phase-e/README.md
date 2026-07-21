# Phase E — evidence

Screenshots proving the serving layer (`sm_energy` semantic model + `rpt_energy` report).
Catalogued as captured.

## E6 — Direct Lake verification

| File | What it proves |
|---|---|
| `e6-storage-mode.png` | **The model is Direct Lake, and the star schema is what we designed.** The web model view shows all six gold tables with the four relationships drawn — `1` on the dim side, `*` on the fact side, single-direction arrows — and the Properties pane for `fact_price_hourly` reads **Storage mode: Direct Lake**. Three design decisions are visible in the same frame: `dim_indicator` sits **disconnected** (deliberate — no fact carries an indicator column), the measures live on their related facts (`Total/Peak Demand` + `Demand YoY %` on `fact_demand_daily`, `Renewables Share %` + `Total Generation` on `fact_generation_daily`, the four price measures on `fact_price_hourly`), and the joins are on **natural keys** (`date`, `technology`) rather than surrogates. |
| `e6-report-rendered.png` | **The report renders — which on Direct Lake *on OneLake* is the no-fallback proof.** That storage mode has no DirectQuery fallback path at all, so a query it couldn't serve directly would error rather than silently downgrade. The Demand page renders `Total Demand` by month across 2023–2026 with `Peak Demand` (867K MWh) and `Demand YoY %` cards and a year slicer. |

**Stronger than a screenshot:** the storage mode is provable from the committed definition
itself — every table partition in `sm_energy.SemanticModel/definition/tables/*.tmdl` carries
`mode: directLake` with `expressionSource: 'DirectLake - lh_energy'`, and `model.tmdl` carries
`annotation PBI_ProTooling = ["DirectLakeOnOneLakeInWeb", ...]`. Screenshots can go stale; the
definition in Git cannot.

## Known caveats visible in `e6-report-rendered.png`

These are captured deliberately — the report is pre-formatting (polish deferred to Power BI
Desktop, see the Phase E TODOs in [track-a-progress.md](../../phases/track-a-progress.md)):

1. **`Demand YoY %` reads 40.5%, which is an artifact, not a finding.** With no year selected,
   the measure compares the whole loaded span (2023-01 → 2026-07) against `DATEADD(-1 YEAR)`
   (2022-01 → 2025-07) — but data only starts 2023-01, so it is comparing ~3.5 years of demand
   against ~2.5 years. A YoY card is only meaningful inside a period context; fix by defaulting
   the slicer to a year or by rewriting the card to compare the latest *complete* period.
2. **The line dives at the right edge** because July 2026 is a **partial month** — the current
   month always under-sums until it completes. Filter to complete months or annotate it.

## E8 — portfolio showcase

*(pending — the polished, formatted report pages captured after the Power BI Desktop pass.)*
