# Phase D — Orchestration

**Progress:** tracked per run in [track-a-progress.md](track-a-progress.md) · [track-b-progress.md](track-b-progress.md)
**Days:** D5 (build) + 2 passive days (proof) · **Plan:** [P1 §Phase D](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phase C ✅

## Outcome (done criteria)

- Master pipeline `pl_daily_refresh` runs ingest → DQ gate → silver → gold
      end-to-end from one trigger, params flowing through.
- Daily schedule moved to the master; the old `pl_ingest_daily` schedule disabled.
- **Green in run history two days straight** (scheduled runs, not manual) —
      screenshots.
- Failure alert fires from the master (single alert, not one per child).

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Master shape | `pl_daily_refresh` **invokes** `pl_ingest_daily`, then notebook activities: `nb_bronze_to_silver` ×3 (sequential per indicator) → `nb_dq_gate (silver)` → `nb_gold_build` → `nb_gold_mlv` | Reuses everything as-is; the DQ gate sits **between** silver and gold so bad data never reaches Gold — that's the "data quality gate" story |
| Semantic model refresh | Placeholder only — Direct Lake (Phase E) reads Delta directly, no scheduled refresh activity needed; note this as a drill answer | A refresh activity here would be cargo-culting Import-mode habits |
| Alerting | One Outlook activity on the master's failure path; child pipelines keep theirs but children are no longer scheduled independently | One actionable mail per failed day |
| Two-day proof timing | Schedule flips to the master on D5 → proof lands D6–D7 while Phases E/F run in parallel | Passive evidence; no idle days |

## Steps

### D1 `[YOU]` Build `pl_daily_refresh`

- Folder `orchestration` → **+ New item** → **Data pipeline** → `pl_daily_refresh`.
- Chain with **On success** dependencies, in order:
  1. **Invoke pipeline** → `pl_ingest_daily` (wait on completion = ON).
  2. Three **Notebook** activities → `nb_bronze_to_silver`, base parameter
     `p_indicator` = each indicator; chain them **sequentially** (shared Spark session
     pressure on 64 CU beats parallel here — note actual timings in Gotchas).
  3. **Notebook** → `nb_dq_gate`, `p_stage` = `silver`.
  4. **Notebook** → `nb_gold_build`.
  5. **Notebook** → `nb_gold_mlv`.
- **Failure alert — single-source funnel** (do **not** fan seven `On fail` arrows into
      one activity: Data Factory AND's dependencies from different sources, so the alert
      would only fire if *every* stage failed at once — never, in a chain that stops at the
      first failure. See Gotchas 2026-07-20).
  - **Office 365 Outlook** `alert_on_fail`, one dependency on **`nb_gold_mlv` only**,
        conditions **`Failed` + `Skipped`** (two conditions on one source are OR'd). Any
        upstream failure short-circuits the chain, so the terminal is *Skipped* → alert
        fires exactly once. To: `v_alert_email` (library variable). Subject: generic +
        `@{pipeline().RunId}`; the run link shows the failed stage.
  - **Fail** activity `fail_run`, dependency on `alert_on_fail` (`Succeeded`). A
        succeeding failure-path activity would otherwise flip the pipeline to *Succeeded*
        (Data Factory try/catch semantics); `fail_run` re-fails so Monitor stays red and
        D3's "green means green" detection is honest.
- Manual full run → all green in Monitor, end-to-end (alert + fail_run both *Skipped* on
      success). Screenshot the run detail showing every stage.
- **Prove the alert** with a controlled failure: set `nb_dq_gate_silver` base param
      `p_stage` = `silverX` (invalid → `run_gate` raises on stage validation, no data
      touched) → run → expect one email + pipeline **Failed** + gold stages *Skipped*.
      Revert `p_stage` = `silver`. Screenshot the failed run.
- Commit (`feat(orchestration): master daily refresh pipeline`).

### D2 `[YOU]` Move the schedule

- `pl_ingest_daily` → **Run → Schedule** → **disable/delete** the Phase B schedule.
- `pl_daily_refresh` → **Run → Schedule** → daily **08:00 Europe/Madrid**, end date
      2026-07-31. Commit.

### D3 `[YOU]` Two-day green proof (passive — runs during Phases E/F)

- Morning after day 1: Monitor → scheduled `pl_daily_refresh` run is green;
      screenshot **with the trigger type visible** (scheduled, not manual).
- Morning after day 2: same again. Two consecutive scheduled greens = done
      criterion. If a day fails: fix, note in Gotchas, and the 2-day counter restarts —
      be honest about it.

### D4 `[CLAUDE]` Review + evidence

- Pull; review `pl_daily_refresh` JSON: dependency wiring (nothing accidentally
      parallel), wait-on-completion on the Invoke, alert coverage of all stages.
- Evidence into `docs/evidence/phase-d/`; tick done-criteria, Status ✅, session
      log (include stage-by-stage timings from the first full run — feeds capacity
      notes in Phase G).
- 🎓 **Understanding check:** Claude confirms Gonzalo can explain **why the DQ gate
      sits between silver and gold** (bad data never reaches Gold) and **why no semantic-
      model refresh activity is needed** (Direct Lake reads Delta directly — a common
      Import-mode reflex to avoid). Quick `AskUserQuestion` if either is fuzzy.

## Gotchas & deviations

**2026-07-20 — the "email on any failure" fan-in is a trap (D1).** First build wired
`alert_on_fail` with seven `On fail` arrows, one from each stage. Two documented Data
Factory behaviors break this:

1. **Dependencies from different sources are AND'ed** ([MS Learn](https://learn.microsoft.com/en-us/azure/data-factory/tutorial-pipeline-failure-error-handling),
   [Data Savvy](https://datasavvy.me/2018/10/02/data-factory-v2-activity-dependencies-are-a-logical-and/)).
   Seven `Failed` sources into one activity ⇒ it runs only if all seven are `Failed`
   simultaneously — impossible once the chain short-circuits at the first failure. Alert
   never fires.
2. **A failure-path activity that *succeeds* flips the pipeline to `Succeeded`**
   ([Data Savvy](https://datasavvy.me/2021/02/18/azure-data-factory-activity-failures-and-pipeline-outcomes/))
   — treated as a caught try/catch. So even a *working* alert would turn the red run green.

**Fix — single-source funnel on the terminal's `Skipped` state + a `Fail` activity:**
`alert_on_fail` depends on **`nb_gold_mlv` only**, conditions `Failed` + `Skipped` (same
source ⇒ OR). Any upstream failure short-circuits the chain, leaving the terminal `Skipped`,
so the alert fires exactly once regardless of which stage broke. `fail_run` (Fail activity)
then depends on the alert's success and re-fails, restoring the honest `Failed` outcome.
Proven with a controlled failure (`p_stage=silverX` on the gate — validation raises, no data
touched). *(If a tenant lacks the Fail activity, the legacy workaround is a Web activity
hitting an invalid URL.)*

*(Other expected suspects: notebook session startup per activity — consider session tags /
high-concurrency mode if the chain is slow; Invoke-pipeline wait behavior.)*

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
