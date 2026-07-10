# P2 Phase C — KQL analytics + Real-Time Dashboard

**Status:** ⬜ not started
**Days:** D9–D10 · **Plan:** [P2 §Phase C](../fabric-p2-realtime-intelligence.md) ·
**Requires:** P2 Phase B ✅ (producer scheduled, `demand_rt` MV populated)

## Outcome (done criteria)

- [ ] KQL query set committed as `.kql` files in `streaming/kql/`: deviation per
      interval, rolling 1 h average, daily peak detection, worst-deviation league table.
- [ ] Real-Time Dashboard `rtd_demand` live: demand curve (real vs prevista vs
      programada), deviation gauge, auto-refresh on.
- [ ] Dashboard updates **unattended** across at least a half-day window — proven with
      screenshots at two timestamps ≥ 6 h apart.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Query base | Every query and dashboard tile reads the **materialized view** `demand_rt`, never `demand_rt_raw` | The MV is the deduped truth; querying raw would silently double-count on overlap windows |
| Deviation shape | A reusable `deviation` pattern: pivot series to columns per `ts`, compute `deviation_pct = 100.0 * (real - prevista) / prevista` | One canonical definition, reused by dashboard, Activator (Phase D) and the unification join (Phase E) — no drifting formulas |
| Query storage | Authored in the repo (`streaming/kql/*.kql`), pasted into a **KQL queryset** `kqs_demand` in Fabric | Repo is the durable, reviewable artifact; the queryset is the runtime convenience |
| Dashboard tiles | Base tiles on saved queries with parameters (time range) rather than ad-hoc snippets | Parameters make the half-day-unattended proof honest (no manual tweaks between screenshots) |

## Steps

### C1 `[YOU]` Learn first (~45 min, timeboxed)

- [ ] KQL queryset + Real-Time Dashboard concepts:
      `https://learn.microsoft.com/fabric/real-time-intelligence/dashboard-real-time-create`
- [ ] Skim visualization operators: `render`, and dashboard-side visual config
      (dashboards configure visuals per tile; `render` only affects queryset preview).

### C2 `[CLAUDE]` Author the query set (repo first)

- [ ] On branch `feature/kql-analytics`, write `streaming/kql/` files, each with a
      comment header stating intent and expected shape:
  - `01-deviation-by-interval.kql` — pivot `demand_rt` to `real`/`prevista`/
    `programada` columns per `ts` (`summarize ... by ts` with `take_anyif` or
    `max(case(...))` idiom), compute `deviation_pct`; latest 24 h.
  - `02-rolling-1h-avg.kql` — rolling 1 h mean of `real` per 5-min slot
    (`avg` over a sliding window via `range`/`mv-apply` or the simpler
    `summarize avg(value_mw) by bin(ts, 1h), series` hourly variant — Claude
    implements the true sliding version, keeps the hourly one as a commented
    alternative and explains the difference in the header).
  - `03-daily-peak.kql` — `arg_max(value_mw)` per day for `series == "real"`, with
    the timestamp the peak occurred.
  - `04-worst-deviation-league.kql` — top 20 intervals by `abs(deviation_pct)` over
    the trailing 7 days, with sign and both values shown.
- [ ] PR → `develop`, merge.

### C3 `[YOU]` Validate in a KQL queryset

- [ ] Folder `streaming` → **+ New item** → **KQL queryset** → `kqs_demand`, connect
      to `eh_energy`.
- [ ] Paste each repo query in as a named tab; run all four against live data;
      sanity-check numbers against yesterday's reality (peak demand ~evening,
      deviation mostly within a few %).
- [ ] Anything that needed fixing goes **back into the repo files** (repo is truth) —
      then commit the queryset via Source control
      (`feat(streaming): kql analytics queryset`).

### C4 `[YOU]` Build the Real-Time Dashboard

- [ ] Folder `streaming` → **+ New item** → **Real-Time Dashboard** → `rtd_demand`,
      data source = `eh_energy`.
- [ ] Tiles (each backed by the corresponding repo query, time range as a dashboard
      parameter):
  1. **Live demand curve** — time chart, `real` vs `prevista` vs `programada`,
     last 24 h.
  2. **Deviation now** — stat/gauge tile: latest `deviation_pct`, thresholds
     colored (green < 2 %, amber < 5 %, red ≥ 5 % — tune to observed data).
  3. **Rolling 1 h average** — line over last 24 h.
  4. **Daily peaks** — table or column chart, last 7 days.
  5. **Worst deviations** — league table tile.
- [ ] Dashboard settings → **auto-refresh** ON (e.g. every 5 min; producer feeds every
      10, so 5-min refresh never shows stale-by-design data for long).
- [ ] Commit (`feat(streaming): real-time demand dashboard`).

### C5 `[YOU]` The unattended proof

- [ ] Screenshot the dashboard now (visible clock/timestamp on a tile), note the time.
- [ ] Do **nothing** for ≥ 6 h (leave the schedule running; go do Phase D's learning).
- [ ] Screenshot again ≥ 6 h later — curves advanced, no manual touch. This pair is
      the "it runs unattended" evidence; drop both in `docs/evidence/p2-phase-c/`.

### C6 `[CLAUDE]` 🎓 Understanding check — KQL analytics

- [ ] Quiz (`AskUserQuestion`): why every consumer reads the MV (what breaks if a tile
      reads raw); how the series pivot works and why deviation is a pivot-then-compute,
      not a join-per-row; sliding window vs `bin()` bucketing (query 02's two
      variants); what auto-refresh actually re-executes.
- [ ] Record weak spots for the Phase E drills.

### C7 `[CLAUDE]` Close + 📣 capture

- [ ] Evidence normalized into `docs/evidence/p2-phase-c/`; tick done-criteria,
      Status ✅, session log.
- [ ] 📣 **Portfolio (capture, not publish):** the two-timestamp dashboard pair and
      one queryset screenshot are the streaming visuals for the Phase E portfolio
      update — name them and keep them.

## Gotchas & deviations

*(expected suspects: dashboard parameter syntax vs raw KQL differences; tile time-range
parameter defaults; auto-refresh minimum interval on trial)*

## Session log

- 2026-07-10 — Guide written during repo prep. Nothing built yet.
