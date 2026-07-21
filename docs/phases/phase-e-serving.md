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
| Storage mode | **Direct Lake on OneLake** (not Direct Lake on SQL) — ⚠️ **corrected 2026-07-21**, see Gotchas | Reads Delta straight from OneLake, so no SQL-endpoint metadata-sync lag and better DAX plans. Decisively: it has **no DirectQuery fallback path at all**, which satisfies the "no fallback" requirement *by construction* |
| Fallback policy | ~~Model property **Direct Lake behavior = Direct Lake only**~~ — **N/A on Direct Lake on OneLake** | That toggle only exists for Direct Lake **on SQL**, the mode that *can* fall back. On OneLake a query that can't be served directly errors; there is nothing to configure |
| Date handling | Mark `dim_date` as the model's date table. **Auto date/time is not a web-modeling setting** — see Gotchas | Star-schema hygiene. The auto date/time toggle lives in Power BI **Desktop**; in a web-authored model the equivalent is the `__PBI_TimeIntelligenceEnabled` annotation in TMDL |
| Derived columns | Any column the model needs must be built in `nb_gold_build` (Spark), never in the model | **Direct Lake supports no calculated columns.** Same "shape it in the lake" rule that keeps us off SQL views |
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

- Open `lh_energy` → toolbar **New semantic model** → name `sm_energy`.
- **The dialog asks for a storage mode: choose Direct Lake on OneLake.** (The other
      option, *Direct Lake on SQL*, routes through the SQL analytics endpoint and is the
      only one that can fall back to DirectQuery — see the Decisions table.)
- Select **only** the `gold` schema objects: 3 dims + 3 facts (leave MLVs out of
      the model for now — aggregates come from measures; revisit only if visuals are
      slow).
- The model opens in the web model editor (or find it in the workspace root
      afterwards — move it to folder `gold`).

### E3 `[YOU]` Model structure

- Relationships (all many-to-one, single direction, fact → dim). **Our Gold has no
      surrogate keys** — it joins on **natural keys**, so the four relationships are:
  - `fact_demand_daily[date]` → `dim_date[date]`
  - `fact_generation_daily[date]` → `dim_date[date]`
  - `fact_generation_daily[technology]` → `dim_technology[technology]`
  - `fact_price_hourly[date]` → `dim_date[date]`
- **`dim_indicator` stays disconnected** — no fact carries an indicator column. That is
      deliberate, not an oversight: the indicator is what *distinguishes the three facts*,
      so it is a table-level fact, not a row-level one. Leave it in the model as
      documentation of the source series.
- Tick **Assume referential integrity** on all four. It promises every many-side key
      exists on the one side, letting the engine use INNER instead of LEFT OUTER joins.
      **Safe here for three specific reasons** — the calendar is a superset of the data,
      `dim_technology` is built as the exact `DISTINCT` set, and the DQ gate enforces
      non-null keys. Break any one of those and orphan rows would be *silently dropped*.
- Mark `dim_date` as **date table** (on its `date` column).
- Hide the raw fact columns that have a measure counterpart.
- ⚠️ **Web modeling does not validate any of this.** It will not check cardinality,
      relationship direction, or whether the marked date column is contiguous. Correctness
      is entirely on the author — which is the argument for reviewing the TMDL in Git (E7).
- ~~Model settings → Direct Lake behavior → Direct Lake only.~~ **N/A** — that property
      exists only for Direct Lake on SQL.

### E4 `[YOU]` Measures (paste, then adjust column names to the actual Gold schema)

- `Total Demand = SUM(fact_demand_daily[demand_mwh])`
- `Peak Demand = MAX(fact_demand_daily[demand_mwh])`
- `Renewables Share % = DIVIDE(CALCULATE(SUM(fact_generation_daily[generation_mwh]), dim_technology[is_renewable] = TRUE()), SUM(fact_generation_daily[generation_mwh]))`
- `Avg Price (€/MWh) = AVERAGE(fact_price_hourly[price_eur_mwh])`
- Format: percentages as %, energy with thousands separators, prices 2 decimals.
      **Don't skip `Min Price` / `Max Price`** — a measure with no `formatString` renders
      with full float noise.
- Sanity-check each measure in a card/table visual against a known month before
      building pages. Ours were checked against the **C7 SQL proof**: `Renewables Share %`
      for 2024-03 must render 65.7% (= the 65.69% the star join and the MLV both produced).
      A measure that disagrees with a committed `.sql` proof is a *measure* bug.

**Four measures the naive version gets wrong** — all learned the hard way at E5, all fixed
in TMDL rather than in the report (⚠️ **corrected 2026-07-21**; see Gotchas):

- `Avg Price 30D` — needs an `ISBLANK` guard, or the rolling window bleeds 30 days past the
      last priced date into an empty future calendar:
      `IF(ISBLANK([Avg Price (€/MWh)]), BLANK(), AVERAGEX(DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -30, DAY), [Avg Price (€/MWh)]))`
- `Demand YoY % (R12)` — the textbook `DATEADD(-1, YEAR)` ratio has **no opinion about
      whether the two windows are comparable**. On a card with nothing selected it divides
      two spans covering different amounts of loaded data and reports confident nonsense.
      Anchor it instead to the last loaded fact date and isolate it from the slicer:

  ```dax
  VAR LastLoaded = CALCULATE(MAX(fact_demand_daily[date]), REMOVEFILTERS())
  VAR CurrEnd    = EOMONTH(LastLoaded, -1)          -- last COMPLETE month
  VAR CurrStart  = EDATE(CurrEnd, -12) + 1
  VAR PriorEnd   = EOMONTH(CurrEnd, -12)
  VAR PriorStart = EDATE(PriorEnd, -12) + 1
  VAR Curr  = CALCULATE([Total Demand], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date], CurrStart, CurrEnd))
  VAR Prior = CALCULATE([Total Demand], REMOVEFILTERS(dim_date), DATESBETWEEN(dim_date[date], PriorStart, PriorEnd))
  RETURN DIVIDE(Curr - Prior, Prior)
  ```

  `REMOVEFILTERS(dim_date)` is load-bearing: the year slicer filters `dim_date[year]`, and
      `DATESBETWEEN` on `dim_date[date]` would **not** override a filter on a different column.
- `Total Demand (Complete Months)` — the monthly trend dives at the right edge because the
      current month is partial. Inside a month bucket `MAX(dim_date[date])` *is* that month's
      last calendar day, which makes the completeness test one line and needs **no new
      column** (Direct Lake has none):
      `IF(MAX(dim_date[date]) <= CALCULATE(MAX(fact_demand_daily[date]), REMOVEFILTERS()), [Total Demand])`
- `Data Through` — hiding the partial month hides freshness, so put it back explicitly.
      Take the **earliest** of the facts' last loaded dates ("every fact is loaded at least
      through here"); the max would let two current indicators hide one lagging behind them.

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
- **Build the visuals in the web editor; do the formatting pass in Power BI Desktop.**
      The web editor is fine for laying out fields but painful for polish. Two rules if you
      split the work that way: finish all **model** changes first (Desktop republish
      overwrites the model definition wholesale), and re-download after any Git-side pull.
- A report page that looks wrong is **not automatically a formatting problem.** Ours
      showed a 40.5% YoY card and a collapsing trend line — both were DAX defects that would
      have survived any amount of visual polish. Diagnose to the layer before styling.

### E6 `[YOU]` Verify Direct Lake (money screenshot)

- Interact with every page. On **Direct Lake on OneLake** there is no fallback path, so a
      query that couldn't be served directly would **error** rather than silently downgrade —
      all pages rendering *is* the proof.
- **Two separate screenshots — they cannot be one frame.** Table properties are only
      visible from the semantic model page, so you can't show a report page and the storage
      mode simultaneously:
  1. Model view, with a fact table selected and the Properties pane showing
     **Storage mode: Direct Lake**.
  2. A rendered report page.
- **Stronger than either screenshot:** the storage mode is provable from the committed
      definition — every partition in `definition/tables/*.tmdl` carries `mode: directLake`,
      and `model.tmdl` carries `annotation PBI_ProTooling = ["DirectLakeOnOneLakeInWeb", …]`.
      Screenshots go stale; the definition in Git does not.

### E7 `[YOU]` + `[CLAUDE]` Sync + review

- `[YOU]` Workspace **Source control → Commit**. Items serialize under the **workspace
      folder** they live in, so having moved both to `gold` at E2/E5 they land at
      `fabric/gold/sm_energy.SemanticModel/` (TMDL) and `fabric/gold/rpt_energy.Report/`
      (PBIR) — not at the repo's `fabric/` root as this guide first assumed.
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

### 2026-07-21 — Fabric now asks *which* Direct Lake, and the answer changes the phase

The **New semantic model** dialog offers **Direct Lake on OneLake** vs **Direct Lake on
SQL**. This guide was written before that split existed and assumed the SQL-endpoint flavour
throughout. Chose **OneLake**: it reads Delta straight from OneLake with no SQL-endpoint
metadata-sync lag, and it has **no DirectQuery fallback path at all**
([MS Learn](https://learn.microsoft.com/en-us/fabric/fundamentals/direct-lake-overview)).

Consequences, all corrected above:

- The `DirectLakeBehavior` / "Direct Lake only" property **does not exist** in this mode —
  it is the knob for the mode that *can* fall back. The "no fallback" claim is now proven
  **by construction** rather than by configuration, which is a stronger claim, not a weaker
  one.
- E6's evidence changes from *"screenshot the Direct Lake only setting"* to *"storage mode =
  Direct Lake + every page renders"*.

**Worth being precise about in an interview:** "Direct Lake has no fallback" is false in
general. Direct Lake **on SQL** falls back — on SQL-endpoint views, unsupported DAX/model
features, and capacity guardrail row limits. Only **on OneLake** is there no fallback path
to take.

### 2026-07-21 — Direct Lake supports no calculated columns

Not a limitation to work around — a rule to design to. Every derived column must be built in
`nb_gold_build` (Spark) and land in the Delta table. It is the same constraint that keeps us
off SQL-endpoint views, and it is why the `Total Demand (Complete Months)` fix at E4 is a
*measure* rather than an `is_complete_month` column.

### 2026-07-21 — Auto date/time is a Power BI Desktop setting, not a web-modeling one

The guide said "disable auto date/time" as if it were a checkbox in the model editor. It is
not — there is no such option in web modeling, and looking for one wastes time.

What was *actually* true here is worse than "N/A": the model was created carrying
`annotation __PBI_TimeIntelligenceEnabled = 1`, i.e. **enabled**, with no UI to turn it off.
Fixed the only way available — editing `model.tmdl` in Git to `= 0` and pulling it back with
*Update all*. Verified first that no visual depended on an auto-generated date hierarchy.

**The general lesson:** TMDL-in-Git is not just an evidence artifact, it is a *control
surface*. It reaches model properties the web editor doesn't expose.

### 2026-07-21 — Fabric merges items **whole**, not line by line (cost: one real conflict)

A semantic model is **one item**. If its definition moves in Git while you are editing it in
the portal, Fabric cannot merge the two — it makes you choose an entire side and discard the
other.

This bit us for real: a Git-side edit to `model.tmdl` was pushed while `sm_energy` was being
edited in the portal. Resolution was to keep the workspace side (`7ed4748`) and then re-apply
the Git-side change on top (`8c02381`) — two commits to land one change.

**Rule: run *Update all* before portal-editing any item whose definition may have moved in
Git.** The same applies in reverse to Power BI Desktop: a Desktop republish overwrites the
model definition wholesale.

### 2026-07-21 — Report visuals bind to measures by **name**

`queryRef` / `nativeQueryRef` / `Property` in each `visual.json` are the measure's *name*, not
its `lineageTag`. Renaming a measure in TMDL therefore breaks every visual using it unless the
report is updated in the same commit. Both items live in Git, so this is a mechanical fix —
but only if you remember to look.

### Pre-existing: the guide's `_key` column names were placeholders

E3 originally specified `fact_*[date_key] → dim_date[date_key]` and an
`[indicator_key]` relationship. Our Gold uses **natural keys** (`date`, `technology`) and no
fact carries an indicator column — `dim_indicator` is intentionally disconnected. Corrected
in place above.

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
