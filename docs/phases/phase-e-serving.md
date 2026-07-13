# Phase E — Serving (Direct Lake + Power BI)

**Progress:** tracked per run in [track-a-progress.md](track-a-progress.md) · [track-b-progress.md](track-b-progress.md)
**Days:** D6 · **Plan:** [P1 §Phase E](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phase C ✅ (Gold populated); Phase D running in background

## Outcome (done criteria)

- Custom **Direct Lake** semantic model over Gold (not the default model):
      relationships + DAX measures.
- Power BI report (3 pages: demand trends, generation mix, price panel) renders in
      **Direct Lake mode with no DirectQuery fallback** — verified, not assumed.
- Measure definitions (TMDL) land in the repo via Git sync; screenshots in evidence.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Model | New custom model `sm_energy` over the `gold` schema only; the auto-created default model stays untouched | Drill answer: the default model is a convenience artifact; a curated model is the deliverable |
| Fallback policy | Model property **Direct Lake behavior = Direct Lake only** | Queries *fail loudly* instead of silently falling back to DirectQuery — if the report renders, the "no fallback" claim is proven by construction |
| Date handling | Mark `dim_date` as the model's date table; disable auto date/time | Star-schema hygiene; auto date/time bloats Direct Lake models |
| XMLA check | First XMLA-dependent moment of the sprint (tenant setting uninspectable — see master plan). If external tooling is blocked, model editing stays in the web editor; note the outcome here | Planned probe from the Day-0 risk register |

## Steps

### E1 `[YOU]` Learn first (~45 min, timeboxed)

- Direct Lake vs Import vs DirectQuery + fallback triggers (the #1 drill):
      `https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview`.
      Key fallback triggers to remember: SQL-endpoint views, unsupported DAX/model
      features, guardrail row counts.

### E1.5 `[CLAUDE]` 🎓 Understanding check — Direct Lake (the #1 drill)

- Claude quizzes Gonzalo (`AskUserQuestion`) on the storage-mode drill:
      **Direct Lake vs Import vs DirectQuery**, what **triggers a fallback** to
      DirectQuery, and why we set **"Direct Lake only"** (fail loudly = proof by
      construction). Diagram the query path (report → semantic model → Delta in the
      lakehouse, no import copy) if useful. This is the interview question recruiters ask
      most — make sure it's airtight.
- Record weak spots for the Phase G drills.

### E2 `[YOU]` Create the custom semantic model

- Open `lh_energy` → **SQL analytics endpoint** view → toolbar **New semantic
      model** → name `sm_energy`.
- Select **only** the `gold` schema objects: 3 dims + 3 facts (leave MLVs out of
      the model for now — aggregates come from measures; revisit only if visuals are
      slow).
- The model opens in the web model editor (or find it in the workspace root
      afterwards — move it to folder `gold`).

### E3 `[YOU]` Model structure

- Relationships (all many-to-one, single direction, fact → dim):
  - `fact_demand_daily[date_key]` → `dim_date[date_key]`
  - `fact_generation_daily[date_key]` → `dim_date[date_key]`
  - `fact_generation_daily[technology_key]` → `dim_technology[technology_key]`
  - `fact_price_hourly[date_key]` → `dim_date[date_key]`
  - facts `[indicator_key]` → `dim_indicator[indicator_key]` where present
- Mark `dim_date` as **date table** (on its date column).
- Hide all key columns and the raw fact columns that have a measure counterpart.
- Model settings → **Direct Lake behavior → Direct Lake only**.

### E4 `[YOU]` Measures (paste, then adjust column names to the actual Gold schema)

- `Total Demand = SUM(fact_demand_daily[demand_mwh])`
- `Peak Demand = MAX(fact_demand_daily[demand_mwh])`
- `Demand YoY % = DIVIDE([Total Demand] - CALCULATE([Total Demand], DATEADD(dim_date[date], -1, YEAR)), CALCULATE([Total Demand], DATEADD(dim_date[date], -1, YEAR)))`
- `Renewables Share % = DIVIDE(CALCULATE(SUM(fact_generation_daily[generation_mwh]), dim_technology[is_renewable] = TRUE()), SUM(fact_generation_daily[generation_mwh]))`
- `Avg Price (€/MWh) = AVERAGE(fact_price_hourly[price_eur_mwh])`
- `Avg Price 30D = AVERAGEX(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -30, DAY), [Avg Price (€/MWh)])`
- Format: percentages as %, energy with thousands separators, prices 2 decimals.
- Sanity-check each measure in a card/table visual against a known month before
      building pages.

### E5 `[YOU]` Report (the showcase surface — apply the wiki's report craft)

- From `sm_energy` → **Create report**. Three pages:
  1. **Demand** — line: `Total Demand` by month (dim_date hierarchy); KPI cards: Peak
     Demand, Demand YoY %; year slicer.
  2. **Generation mix** — 100% stacked area: generation by `dim_technology[technology]`
     over time; card + trend for `Renewables Share %`.
  3. **Prices** — line: `Avg Price (€/MWh)` hourly/daily with `Avg Price 30D` overlay;
     min/max cards; a "prices spike" annotation if the data shows one (it will —
     tell the story).
- Consistent theme, titles that state the takeaway (not "Chart 1"), no default
      gridline noise. Save to folder `gold`, name `rpt_energy`.

### E6 `[YOU]` Verify Direct Lake (money screenshot)

- Interact with every page — with **Direct Lake only** set in E3, any fallback
      would error instead of rendering. All pages render = proof.
- Screenshot the model settings page showing "Direct Lake only" + a rendered
      report page (pair them in evidence).

### E7 `[YOU]` + `[CLAUDE]` Sync + review

- `[YOU]` Workspace **Source control → Commit** (model lands as TMDL under
      `fabric/sm_energy.SemanticModel/`, report as PBIR under
      `fabric/rpt_energy.Report/`).
- `[CLAUDE]` Pull; verify measures are readable in TMDL (quote one in the README —
      "measure definitions reviewable in Git" claim); review relationship definitions;
      evidence into `docs/evidence/phase-e/`; tick done-criteria, Status ✅, session
      log (record the XMLA outcome from the Decisions table).

### E8 `[CLAUDE]` + `[YOU]` 📣 Portfolio — the visual showcase

- `[YOU]` Capture the hero visuals: the three report pages (demand, generation mix,
      prices) and the "Direct Lake only" model setting. If Publish-to-Web is allowed on
      the tenant, grab the embed URL — it turns the portfolio entry from screenshots into
      a live report (see the embed placeholder pattern in `azure-pipeline.mdx`).
- `[CLAUDE]` Update `fabric-energy-lakehouse.mdx` (+ Es mirror): add the report
      screenshots (or live embed), a short "serving layer" section (Direct Lake, curated
      model, DAX measures), and the reviewable-TMDL-measures point. This is the money
      shot — the entry should now read as a complete story end-to-end.
- `[YOU]` Review and commit in the portfolio repo. Consider flipping the entry to
      visible/featured now if you want it live before Phase G's final polish.

## Gotchas & deviations

*(expected suspects: schema-enabled lakehouse + Direct Lake quirks in preview, web
model editor missing a property → try Power BI Desktop / Tabular Editor via XMLA and
record whether XMLA is even open on this tenant)*

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
