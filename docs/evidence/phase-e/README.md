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

## Known caveats visible in `e6-report-rendered.png` — both since fixed

The screenshot is kept as-is: it is the honest "before" of a **pre-formatting** report, and
the two defects it shows are worth documenting because neither was a formatting problem. Both
were **model** defects, and both were fixed in TMDL in Git on 2026-07-21, not in the report.

1. **`Demand YoY %` reads 40.5% — an artifact, not a finding.** The measure was a bare
   `DIVIDE([Total Demand] - CALCULATE([Total Demand], DATEADD(dim_date[date], -1, YEAR)), …)`
   with no opinion about whether the two windows were comparable, so an unfiltered card
   divided two spans covering different amounts of loaded data (data starts 2023-01, the
   calendar runs to 2027). **Fixed** by replacing it with `Demand YoY % (R12)` — a
   self-contained rolling 12 complete months vs the 12 before, anchored to the last loaded
   fact date and isolated from the slicer with `REMOVEFILTERS(dim_date)`, so the two windows
   are equal-span and fully loaded by construction.
2. **The line dives at the right edge** because July 2026 is a **partial month** — the current
   month under-sums until it completes. **Fixed** with `Total Demand (Complete Months)`:
   inside a month bucket `MAX(dim_date[date])` is that month's last calendar day, so comparing
   it to the last loaded fact date is a one-line completeness test. No new column was needed,
   which matters — **Direct Lake supports no calculated columns**, so a column-based fix would
   have meant a Spark rebuild of `nb_gold_build`.

Hiding the partial month costs visible freshness, so a `Data Through` measure was added
alongside: the **earliest** of the three facts' last loaded dates ("every fact is loaded at
least through here"). Taking the max instead would let two current indicators hide one lagging
behind them.

**The transferable lesson:** a report that looks wrong is not automatically a formatting
problem. Both of these would have survived any amount of visual polish, because the defect was
in what the DAX *claimed*, not in how it was drawn.

## E8 — portfolio showcase

*(pending — the polished, formatted report pages captured after the Power BI Desktop pass.)*
