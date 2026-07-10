# P2 — Real-Time Intelligence extension (D8–D11)

Last updated: 2026-07-10 · Part of [[fabric-portfolio-plan]] · Repo: `fabric-energy-lakehouse` (`streaming/`)

**Goal:** a live streaming path on the flagship's domain — REE's 10-minute national demand
feed (`demanda/demanda-tiempo-real`: real, forecast *prevista*, scheduled *programada*) →
Eventstream → Eventhouse/KQL → Real-Time Dashboard + **Activator** alert when actual
demand deviates from forecast. Covers the Kafka/streaming differentiator from
[[junior-de-market-spain-2026-07]] with zero infra cost, and the KQL third of DP-700.

**Minimum shippable (cut line):** Eventstream → Eventhouse → one KQL query set + dashboard;
Activator alert becomes stretch.

## Phase A — KQL foundations (D8, half day)

- Learn first: Eventhouse/KQL DB concepts, KQL basics (`summarize`, `bin`, `join`,
  time-window semantics), update policies vs KQL materialized views, when Eventhouse beats
  Lakehouse (append-heavy, time-indexed, seconds-latency).
- Drill: translate five of your Gold SQL queries into KQL by hand.

## Phase B — Stream ingestion (D8–D9)

- Producer: scheduled Fabric notebook (every 10 min) fetching the latest
  `demanda-tiempo-real` slice and posting to an **Eventstream custom endpoint**
  (Event Hub-compatible); dedup by timestamp so overlapping polls are safe.
  Document honestly: this is *poll-to-stream bridging* (the API has no push) — the
  Eventstream→Eventhouse leg is the real streaming pattern being demonstrated.
- Eventstream: source = custom endpoint; event processing (rename/typed columns,
  derived `deviation_pct` field); destination = Eventhouse table `demand_rt`.
- **Done:** rows visibly arriving each cycle; a duplicate poll produces no duplicate rows
  (update policy or dedup materialized view — explain which and why).

## Phase C — KQL analytics + dashboard (D9–D10)

- KQL query set (committed as `.kql`): deviation real-vs-prevista per interval, rolling
  1 h average, daily peak detection, worst-deviation league table.
- **Real-Time Dashboard**: live demand curve (real vs prevista vs programada),
  deviation gauge, auto-refresh; base queries on a KQL materialized view.
- **Done:** dashboard updates unattended across at least a half-day window (screenshots
  at two times prove it).

## Phase D — Activator (D10)

- Rule: `|real − prevista| / prevista > threshold` sustained for 2 consecutive intervals
  → email/Teams alert. Fire it for real (pick a threshold today's data will cross), keep
  a sensible threshold configured afterwards.
- **Done:** screenshot of a genuinely fired alert + the received notification.
- Hook for P4: the alert log is what the Fabric App will acknowledge/annotate.

## Phase E — Unification + evidence (D11)

- Expose `demand_rt` to the lakehouse (OneLake availability / shortcut) and join it with
  Gold `dim_date`/`fact_demand_daily` in a notebook: intraday stream vs daily batch —
  the "one copy, many engines" OneLake story, told concretely.
- Evidence pack: `.kql` files, dashboard/Activator/Eventstream screenshots, short
  recording, README section with architecture diagram update.
- Wiki note: create [[fabric-rti-kql]].

## Interview drills

Eventstream vs Azure Event Hubs vs Kafka (protocol compatibility, when each); Eventhouse
vs Lakehouse storage/latency trade-offs; KQL vs SQL mental model; update policy vs
materialized view; exactly-once-ish dedup strategies for at-least-once feeds; Activator
concepts (events, conditions, actions); how you'd scale this to per-region streams
(hint: Eventstream derived streams + partitioning).
