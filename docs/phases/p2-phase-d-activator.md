# P2 Phase D — Activator alert

**Status:** ⬜ not started
**Days:** D10 · **Plan:** [P2 §Phase D](../fabric-p2-realtime-intelligence.md) ·
**Requires:** P2 Phase C ✅ (dashboard live, deviation query canonical)

## Outcome (done criteria)

- [ ] Activator rule live: sustained forecast deviation → email/Teams notification.
- [ ] The alert **genuinely fired once** — screenshot of the fired event in Activator
      *and* the received notification, side by side in evidence.
- [ ] A sensible ongoing threshold configured after the test-fire; fired-alert history
      exported to `streaming/data/alerts_fired.json` (P4's seed data).

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Rule source | **Set alert** from the deviation tile on `rtd_demand` (Activator over the dashboard query) | The tile already computes canonical `deviation_pct`; alerting on it means one definition everywhere. Fallback if tile alerts are limited: Activator item on the Eventstream — record the switch here |
| Condition | `abs(deviation_pct)` **becomes greater than** threshold, sustained **20 min** (2 × 10-min producer cycles) | The plan's "2 consecutive intervals"; sustain-for filters single-point blips — the difference between an alert and noise is the interview point |
| Test-fire method | Temporarily set the threshold **below today's observed typical deviation** (read it off the league table), let it fire naturally, then raise to the keeper value | Fires the real end-to-end path — no synthetic events, no faked screenshot |
| Keeper threshold | Decide from data: just above the 7-day p95 of `abs(deviation_pct)` (league-table query tells you) | A threshold with a stated statistical rationale reads senior; note the number and its basis here: ______ |
| Action | Email first (guaranteed on the trial account); try Teams as second action, log outcome | P1 Phase B already probed Office 365 licensing; reuse what worked |
| P4 hook | Every fired alert gets captured into `streaming/data/alerts_fired.json` (`{fired_at, deviation_pct, threshold, status: "new"}`) | P4's grid-ops console seeds its `AlertAck` inbox from this file — the cross-project integration story |

## Steps

### D1 `[YOU]` Learn first (~45 min, timeboxed)

- [ ] Activator concepts — events, objects, conditions, actions:
      `https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/activator-introduction`
- [ ] Alerting from a Real-Time Dashboard:
      `https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/activator-get-data-real-time-dashboard`

### D1.5 `[CLAUDE]` 🎓 Understanding check — Activator

- [ ] Quiz (`AskUserQuestion`): Activator's event → condition → action model; what
      "becomes greater than" means vs "is greater than" (edge vs level trigger) and
      why edge-triggering prevents notification storms; where the 20-min sustain
      lives; what happens if the producer stops (does silence alert? — no, and why
      that's a monitoring gap worth naming).
- [ ] Record weak spots for Phase E drills.

### D2 `[YOU]` Create the rule

- [ ] Open `rtd_demand` → deviation tile → **⋯ → Set alert** (opens Activator pane).
- [ ] Condition: `abs deviation_pct` *becomes greater than* `<test threshold>` —
      read today's typical deviation off the league table first and set the test
      threshold just below it so it will cross within hours.
- [ ] Add the sustain window: condition must hold **20 minutes** (UI: "for each …
      when … stays/occurs" phrasing varies in preview — record actual wording here).
- [ ] Action: **Email** to your address; message includes the deviation value and
      timestamp. Optionally add Teams as a second action.
- [ ] Save — this creates an **Activator item**; move it to folder `streaming`, name
      it `act_demand_deviation`. Commit via Source control if it appears as a change
      (`feat(streaming): demand deviation alert`).

### D3 `[YOU]` Let it fire (for real)

- [ ] Wait for the natural crossing (check the dashboard occasionally; today's data
      *will* cross a just-below-typical threshold).
- [ ] When it fires: screenshot ① the Activator item's fired-events view and ② the
      received email/Teams message. Both into `docs/evidence/p2-phase-d/`.
- [ ] Raise the threshold to the keeper value from the Decisions table; confirm the
      rule stays **on** through trial end.

### D4 `[YOU]` + `[CLAUDE]` Capture history for P4

- [ ] `[YOU]` From the Activator fired-events view, note every firing (time,
      deviation, threshold). Expect a handful once the keeper threshold is in.
- [ ] `[CLAUDE]` Write them into `streaming/data/alerts_fired.json` (schema in the
      Decisions table), commit (`feat(streaming): fired-alert history for grid-ops seed`).
      Append new firings whenever they happen through D18 — P4 Phase B imports this
      file.

### D5 `[CLAUDE]` Close the phase

- [ ] Evidence normalized; tick done-criteria, Status ✅, session log (record actual
      fire time, threshold used, notification latency).

## Gotchas & deviations

*(expected suspects: tile-level Set alert not exposing the sustain window → build the
rule inside the Activator item instead; email action landing in junk; Activator item
Git sync unsupported)*

## Session log

- 2026-07-10 — Guide written during repo prep. Nothing built yet.
