# Phase D — Orchestration

**Status:** ⬜ not started
**Days:** D5 (build) + 2 passive days (proof) · **Plan:** [P1 §Phase D](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phase C ✅

## Outcome (done criteria)

- [ ] Master pipeline `pl_daily_refresh` runs ingest → DQ gate → silver → gold
      end-to-end from one trigger, params flowing through.
- [ ] Daily schedule moved to the master; the old `pl_ingest_daily` schedule disabled.
- [ ] **Green in run history two days straight** (scheduled runs, not manual) —
      screenshots.
- [ ] Failure alert fires from the master (single alert, not one per child).

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Master shape | `pl_daily_refresh` **invokes** `pl_ingest_daily`, then notebook activities: `nb_bronze_to_silver` ×3 (sequential per indicator) → `nb_dq_gate (silver)` → `nb_gold_build` → `nb_gold_mlv` | Reuses everything as-is; the DQ gate sits **between** silver and gold so bad data never reaches Gold — that's the "data quality gate" story |
| Semantic model refresh | Placeholder only — Direct Lake (Phase E) reads Delta directly, no scheduled refresh activity needed; note this as a drill answer | A refresh activity here would be cargo-culting Import-mode habits |
| Alerting | One Outlook activity on the master's failure path; child pipelines keep theirs but children are no longer scheduled independently | One actionable mail per failed day |
| Two-day proof timing | Schedule flips to the master on D5 → proof lands D6–D7 while Phases E/F run in parallel | Passive evidence; no idle days |

## Steps

### D1 `[YOU]` Build `pl_daily_refresh`

- [ ] Folder `orchestration` → **+ New item** → **Data pipeline** → `pl_daily_refresh`.
- [ ] Chain with **On success** dependencies, in order:
  1. **Invoke pipeline** → `pl_ingest_daily` (wait on completion = ON).
  2. Three **Notebook** activities → `nb_bronze_to_silver`, base parameter
     `p_indicator` = each indicator; chain them **sequentially** (shared Spark session
     pressure on 64 CU beats parallel here — note actual timings in Gotchas).
  3. **Notebook** → `nb_dq_gate`, `p_stage` = `silver`.
  4. **Notebook** → `nb_gold_build`.
  5. **Notebook** → `nb_gold_mlv`.
- [ ] **Office 365 Outlook** activity fed by **On fail** from every stage (select all
      activities as sources, red dependencies). To: `v_alert_email` (library variable).
      Subject includes `@{pipeline().RunId}` + which stage (use
      `@{coalesce(...)}`-style or keep it simple: one generic subject, the run link
      shows the failed stage).
- [ ] Manual full run → all green in Monitor, end-to-end. Screenshot the run detail
      showing every stage.
- [ ] Commit (`feat(orchestration): master daily refresh pipeline`).

### D2 `[YOU]` Move the schedule

- [ ] `pl_ingest_daily` → **Run → Schedule** → **disable/delete** the Phase B schedule.
- [ ] `pl_daily_refresh` → **Run → Schedule** → daily **08:00 Europe/Madrid**, end date
      2026-07-31. Commit.

### D3 `[YOU]` Two-day green proof (passive — runs during Phases E/F)

- [ ] Morning after day 1: Monitor → scheduled `pl_daily_refresh` run is green;
      screenshot **with the trigger type visible** (scheduled, not manual).
- [ ] Morning after day 2: same again. Two consecutive scheduled greens = done
      criterion. If a day fails: fix, note in Gotchas, and the 2-day counter restarts —
      be honest about it.

### D4 `[CLAUDE]` Review + evidence

- [ ] Pull; review `pl_daily_refresh` JSON: dependency wiring (nothing accidentally
      parallel), wait-on-completion on the Invoke, alert coverage of all stages.
- [ ] Evidence into `docs/evidence/phase-d/`; tick done-criteria, Status ✅, session
      log (include stage-by-stage timings from the first full run — feeds capacity
      notes in Phase G).
- [ ] 🎓 **Understanding check:** Claude confirms Gonzalo can explain **why the DQ gate
      sits between silver and gold** (bad data never reaches Gold) and **why no semantic-
      model refresh activity is needed** (Direct Lake reads Delta directly — a common
      Import-mode reflex to avoid). Quick `AskUserQuestion` if either is fuzzy.

## Gotchas & deviations

*(expected suspects: notebook session startup per activity — consider session tags /
high-concurrency mode if the chain is slow; Invoke-pipeline wait behavior)*

## Session log

*(one dated line per session)*
