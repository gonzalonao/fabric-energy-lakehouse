# P2 Phase B — Stream ingestion

**Status:** ⬜ not started
**Days:** D8–D9 · **Plan:** [P2 §Phase B](../fabric-p2-realtime-intelligence.md) ·
**Requires:** P2 Phase A ✅

## Outcome (done criteria)

- [ ] Rows visibly arriving in `eh_energy` each 10-minute producer cycle (screenshot
      of row counts growing across two cycles).
- [ ] A deliberately duplicated poll produces **no duplicate rows** in the deduped
      surface — proven, with the mechanism (materialized view) explained in this file.
- [ ] Producer schedule active with an end date at trial expiry; the honest
      "poll-to-stream bridging" paragraph committed in `streaming/README.md`.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Producer | Scheduled Fabric notebook `nb_rt_producer` (every 10 min) fetching the REE real-time feed and posting to an **Eventstream custom endpoint** | The API has no push; a notebook is the cheapest honest bridge. Documented as *poll-to-stream bridging* — the Eventstream→Eventhouse leg is the streaming pattern being demonstrated |
| Poll window | Each poll fetches a **2-hour lookback** (now−2 h → now), not just the newest slice | The `Real` series lags and backfills (probe on 2026-07-10: `Prevista`/`Programada` publish the full day, `Real` trails ~1–2 h); overlap self-heals gaps and late values — at the price of guaranteed duplicates, handled below |
| Dedup mechanism | Raw events land in `demand_rt_raw`; a **KQL materialized view** `demand_rt` = `arg_max(ingested_at, *) by ts, series` serves all queries | Dedup must work *across* ingestion batches → materialized view, not update policy (per-batch only). `arg_max` on ingestion time also means late corrections win — the right semantics for a revising feed |
| Event schema | One event per (timestamp × series): `ts` (datetime), `series` (string: `real`/`prevista`/`programada`), `value_mw` (real) | Long format streams and dedups naturally; `deviation_pct` is **derived in KQL** (Phase C), not in the event — keeping the raw stream raw |
| Secret handling | Eventstream connection string stored in `lh_energy` → **Files** `config/eventstream_conn.txt`; the notebook reads it at runtime | No Key Vault on a trial; a Variable Library value would sync to Git in plain text. Lakehouse Files are data — never synced by Git integration. Documented as trial-grade with the production answer (Key Vault + `notebookutils.credentials`) in the README |
| Producer transport | `azure-eventhub` Python SDK via inline `%pip install` in the notebook | Custom endpoints are Event Hub–compatible; the SDK handles batching/retries. Fallback if `%pip` is blocked: HTTPS POST with a hand-built SAS token (pure stdlib) — note here if used |

## REE real-time feed reference (probed 2026-07-10)

`GET https://apidatos.ree.es/es/datos/demanda/demanda-tiempo-real?start_date=<YYYY-MM-DDTHH:mm>&end_date=<YYYY-MM-DDTHH:mm>&time_trunc=hour`
— tokenless, `Accept: application/json`.

Response: `included[]` carries one entry per series — `Real` (id 2037), `Prevista`
(2052), `Programada` (2053), `Programada total` (2054, ignored) — each with
`attributes.values[] = {value, datetime}` at **5-minute grain** (288/day), local-time
offsets (`+02:00` in summer). `Real` arrives with a lag and is revised; forecast series
publish the whole day upfront. Producer normalizes datetimes to **UTC** before sending
(same rule as P1 Silver).

Smoke test (PowerShell):
`Invoke-RestMethod "https://apidatos.ree.es/es/datos/demanda/demanda-tiempo-real?start_date=2026-07-18T00:00&end_date=2026-07-18T23:59&time_trunc=hour"`

## Steps

### B1 `[YOU]` Learn first (~1 h, timeboxed)

- [ ] Eventstream anatomy — sources, event processing operations, destinations,
      derived streams: `https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview`
- [ ] Custom endpoint source specifically (the Event Hub/AMQP/Kafka triple protocol):
      `https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-custom-app`
- [ ] Eventhouse destination + ingestion modes:
      `https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-destination-kql-database`

### B1.5 `[CLAUDE]` 🎓 Understanding check — bridging & dedup

- [ ] Diagram the full topology: REE API → `nb_rt_producer` (10-min schedule, 2-h
      lookback) → Eventstream `es_demand_rt` custom endpoint → processing → Eventhouse
      `demand_rt_raw` → MV `demand_rt` → consumers.
- [ ] Quiz (`AskUserQuestion`): why the lookback window guarantees duplicates and why
      that's the *right* trade; why dedup lives in a **materialized view** and not an
      update policy or the producer; what "at-least-once + idempotent consumer" means
      and where each half lives in this design; what part of this is honestly
      *streaming* and what part is polling.
- [ ] Record weak spots for P2 Phase E drills.

### B2 `[YOU]` Eventstream with custom endpoint source

- [ ] Folder `streaming` → **+ New item** → **Eventstream** → `es_demand_rt`
      (skip sample data if offered).
- [ ] On the canvas: **Add source → Custom endpoint** (may be labeled *Custom app*),
      name `src_producer`, add.
- [ ] **Publish** the eventstream (details/keys only appear on published streams).
- [ ] Select the custom endpoint node → **Details** pane → **Keys** → copy the
      **Event Hub–compatible connection string** (primary) and note the **Event hub
      name** (a GUID-ish string) — both are needed by the producer.
- [ ] Store the secret where the notebook will read it: open `lh_energy` → Files →
      create folder `config` → upload a one-line text file `eventstream_conn.txt`
      containing `<connection string>|<eventhub name>`. **Never** paste either into a
      notebook cell, commit, or Variable Library.
- [ ] Commit via Source control (`feat(streaming): eventstream with custom endpoint source`).

### B3 `[YOU]` → `[CLAUDE]` Producer notebook (P1 hybrid flow)

- [ ] `[YOU]` In folder `streaming`: **+ New item** → **Notebook** → `nb_rt_producer`,
      attach `lh_energy` as default lakehouse, commit the empty shell.
- [ ] `[CLAUDE]` Pull; write the notebook in Git `.py` format on branch
      `feature/rt-producer`; PR → `develop`; merge. Contents:
  - `%pip install azure-eventhub` first cell (session-scoped).
  - Typed helpers (house style, notebook-practical): `fetch_window(start, end)` →
    parsed JSON; `to_events(payload)` → list of `{ts, series, value_mw}` dicts with
    UTC-normalized ISO timestamps, series mapped `Real→real`, `Prevista→prevista`,
    `Programada→programada`, `Programada total` dropped; `read_conn()` from
    `Files/config/eventstream_conn.txt`; `send(events)` via `EventHubProducerClient`
    batching.
  - Main cell: window = `utcnow−2h → utcnow`, fetch → transform → send; log counts
    with `logging`, exit via `notebookutils.notebook.exit(json.dumps(summary))`.
  - Retry: one retry on HTTP failure, then raise — the 10-min schedule is the real
    retry loop; **no** infinite retries against REE (politeness, same spirit as P1).
- [ ] `[YOU]` **Source control → Update all**; run `nb_rt_producer` once manually.
      Expected: ~`3 series × ~24 slots` events sent, summary JSON in the cell output.

### B4 `[YOU]` Wire Eventstream → Eventhouse

- [ ] Open `es_demand_rt` → edit mode. Between source and destination add
      **Manage fields**: keep/rename to exactly `ts` (DateTime), `series` (String),
      `value_mw` (Double). (Skip a derived deviation field — deviation is a *join*
      across series, out of scope for per-event processing; it's KQL's job in Phase C.)
- [ ] **Add destination → Eventhouse** → workspace `ws-energy-dev` → KQL DB
      `eh_energy` → **create new table** `demand_rt_raw`; ingestion mode: direct
      ingestion is fine (processing happens before the destination). **Publish**.
- [ ] Run `nb_rt_producer` again → open `eh_energy` →
      `demand_rt_raw | summarize count(), max(ts)` → rows present. Screenshot.
- [ ] Commit (`feat(streaming): route producer events into eventhouse`).

### B5 `[YOU]` + `[CLAUDE]` Dedup materialized view

- [ ] `[CLAUDE]` Write `streaming/kql/demand_rt_mv.kql` (and PR it):

  ```kql
  .create materialized-view with (backfill=true) demand_rt on table demand_rt_raw
  {
      demand_rt_raw
      | summarize arg_max(ingestion_time(), *) by ts, series
  }
  ```

  plus a verification query pair (raw count vs distinct `(ts, series)` count vs MV
  count). Adjust to the actual ingestion-time column if `ingestion_time()` isn't
  enabled on the table (`.alter table demand_rt_raw policy ingestiontime true` first —
  Claude includes both statements).
- [ ] `[YOU]` Run the control commands in the `eh_energy` query pane. Verify
      `demand_rt | count` ≤ `demand_rt_raw | count` while
      `distinct (ts, series)` counts match between MV and raw.

### B6 `[YOU]` Prove the dedup (money screenshot)

- [ ] Run `nb_rt_producer` **twice back-to-back** (identical window → near-total
      duplicates). Screenshot: `demand_rt_raw | count` grows both times,
      `demand_rt | summarize count() by bin(ts, 1h)` unchanged after the second run.
- [ ] Paste the two counts + timestamps into this file under Gotchas as the recorded
      proof, alongside the screenshot in evidence.

### B7 `[YOU]` Schedule the producer

- [ ] `nb_rt_producer` → **Run → Schedule**: repeat **every 10 minutes**, start now,
      end **2026-07-31** (trial end). If the notebook scheduler won't go below hourly
      on the trial, wrap the notebook in a one-activity pipeline `pl_rt_producer` in
      folder `streaming` and schedule that instead — record which route worked here.
- [ ] After ≥ 30 min: **Monitor** shows green runs every 10 min; `demand_rt` max(ts)
      advances. Screenshot run history.
- [ ] Commit anything pending (`feat(streaming): schedule 10-min producer`).

### B8 `[CLAUDE]` Review + evidence + honest docs

- [ ] Pull `develop`; review notebook + eventstream definition (no secrets anywhere in
      `/fabric` — grep for `Endpoint=sb://`).
- [ ] Write `streaming/README.md`: topology diagram, the **poll-to-stream bridging**
      paragraph (what's real streaming here and what's a bridge, and why that's the
      correct engineering call for a pull-only API), dedup design, secret-handling
      trade-off and its production upgrade path.
- [ ] Evidence into `docs/evidence/p2-phase-b/`; tick done-criteria, Status ✅,
      session log. 📣 **Portfolio (capture, not publish):** keep the dedup-proof pair
      and the green 10-min run history named for the Phase E write-up.

## Gotchas & deviations

*(expected suspects: custom endpoint keys UI moved; `%pip` cold-start latency on 10-min
schedules; `ingestion_time()` policy off by default; local-time offsets in `datetime`
parsing — the +02:00 must not be dropped)*

## Session log

- 2026-07-10 — Guide written during repo prep; REE real-time endpoint probed (5-min
  grain, Real lags forecasts, 4 series). Nothing built yet.
