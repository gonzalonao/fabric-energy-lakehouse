# P2 Phase E — Unification + evidence

**Status:** ⬜ not started
**Days:** D11 · **Plan:** [P2 §Phase E](../fabric-p2-realtime-intelligence.md) ·
**Requires:** P2 Phases B–D ✅ (D can be closed in parallel if the keeper alert is set)

## Outcome (done criteria)

- [ ] `demand_rt` visible from the lakehouse via OneLake availability + shortcut; a
      notebook joins intraday stream with Gold daily batch — the "one copy, many
      engines" story, executed.
- [ ] Evidence pack complete: `.kql` files, Eventstream/dashboard/Activator
      screenshots, short recording; README architecture updated with the streaming lane.
- [ ] Wiki note `wiki/learning/fabric/fabric-rti-kql.md` created; P2 interview drills
      run out loud.
- [ ] 📣 Portfolio entry updated with the streaming section.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Exposure path | Enable **OneLake availability** on `demand_rt_raw` (and/or the MV if supported), then a **schema shortcut** into `lh_energy` under schema `silver` as `demand_rt` | OneLake availability writes Delta to OneLake; the shortcut makes it queryable from Spark/SQL endpoint with zero copies — the exact claim being demonstrated. If MV-level availability isn't supported, shortcut the raw table and dedup in the join notebook (record which) |
| Join demo | Notebook `nb_stream_vs_batch` (folder `streaming`): today's intraday curve (stream) vs same-day-of-week daily averages from `gold.fact_demand_daily` (batch) | Small, visual, and it forces the cross-engine read (KQL-fed Delta + Gold Delta in one Spark session) |
| Recording scope | 45–60 s: dashboard live-refreshing → Activator fired event → the join notebook output | P2's demo is separate from P1's; both link from the README |

## Steps

### E1 `[YOU]` Expose the stream to OneLake

- [ ] `eh_energy` → table `demand_rt_raw` → enable **OneLake availability** (data
      pane toggle). Note the lag: only data ingested *after* enabling flows to OneLake
      unless backfill is offered — record behavior here.
- [ ] In `lh_energy`: Tables → schema `silver` → **New table shortcut** → OneLake →
      `eh_energy` → `demand_rt_raw`; name the shortcut `demand_rt`.
- [ ] Verify: `SELECT TOP 10 * FROM silver.demand_rt` on the SQL endpoint returns
      rows. Screenshot.

### E2 `[YOU]` → `[CLAUDE]` The unification notebook (hybrid flow)

- [ ] `[YOU]` Create empty notebook `nb_stream_vs_batch` in folder `streaming`,
      attach `lh_energy`, commit.
- [ ] `[CLAUDE]` Pull; write on `feature/stream-vs-batch`; PR → merge:
  - Read `silver.demand_rt` (dedup by `(ts, series)` if shortcutting raw — mirror
    the MV logic), filter `series = 'real'`, today.
  - Read `gold.fact_demand_daily` + `dim_date`; compute the average daily profile
    for the same weekday across the loaded history.
  - Output: one comparison table + one inline chart (today's intraday curve vs
    historical daily-average line); a short markdown cell stating the OneLake
    one-copy point where the two engines met.
- [ ] `[YOU]` Update all, run it, screenshot the chart.

### E3 `[CLAUDE]` README + architecture update

- [ ] Extend the repo `README.md` architecture Mermaid with the streaming lane:
      REE 5-min feed → producer notebook → Eventstream → Eventhouse (raw → MV) →
      dashboard + Activator; OneLake-availability arrow back into `lh_energy`.
- [ ] Add a "Real-Time Intelligence (P2)" README section: what was built, the honest
      poll-to-stream paragraph (link `streaming/README.md`), evidence links.
- [ ] PR → merge.

### E4 `[YOU]` + `[CLAUDE]` Evidence pack + recording

- [ ] `[YOU]` Record 45–60 s per the Decisions row (silent, captions). Remaining
      screenshots captured now if any are missing — **the workspace dies in August**.
- [ ] `[CLAUDE]` Compress/place the recording (same rules as P1 Phase G: < 10 MB in
      repo, else GitHub release), normalize `docs/evidence/p2-phase-*/`, commit.

### E5 `[CLAUDE]` Wiki note + drills

- [ ] Create `wiki/learning/fabric/fabric-rti-kql.md`: Eventhouse/Eventstream/
      Activator patterns that worked, dedup-by-MV design, gotchas harvested from the
      four P2 phase files, and **written-out answers to the P2 interview drills**
      (Eventstream vs Event Hubs vs Kafka; Eventhouse vs Lakehouse; KQL vs SQL mental
      model; update policy vs MV; at-least-once dedup; Activator model; scaling to
      per-region streams via derived streams + partitioning).
- [ ] Update the wiki learning index.
- [ ] `[YOU]` Run the P2 drills out loud, cold. Stumbled: ______ → re-read the note,
      repeat tomorrow.

### E6 `[CLAUDE]` + `[YOU]` 📣 Portfolio + CV touchpoint

- [ ] `[CLAUDE]` Update `../../portfolio/astro/src/content/projects/fabric-energy-lakehouse.mdx`
      (+ Es mirror): add the streaming section — dashboard pair (the ≥ 6 h-apart
      proof), fired-alert shot, one paragraph on the Eventstream→Eventhouse design
      and the honest bridging note. Same entry as P1, extended — one coherent
      batch + streaming story.
- [ ] `[YOU]` Review, commit, deploy.
- [ ] `[CLAUDE]` CV (`../../jobsearch/CVs/Master`): P1's bullet grows the phrase
      "+ Real-Time Intelligence extension (Eventstream, KQL, Activator)" — draft it;
      `[YOU]` confirm. (Full CV realignment still happens once after D21, per the
      master-plan CV rule.)

### E7 `[CLAUDE]` Close P2

- [ ] All four P2 phase files + the phases README index set to final status; session
      logs complete. **P2 closed — P3 starts from
      `../../../fabric-plan-fpna/docs/phases/`.** The producer schedule and Activator
      rule stay running through trial end (they feed P4's seed file).

## Gotchas & deviations

*(expected suspects: OneLake availability lag/backfill behavior; MV not exposable —
shortcut raw instead; shortcut schema placement quirks on schema-enabled lakehouses)*

## Session log

- 2026-07-10 — Guide written during repo prep. Nothing built yet.
