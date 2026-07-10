# P2 Phase A — KQL foundations

**Status:** ⬜ not started
**Days:** D8, half day (≈ 2026-07-18) · **Plan:** [P2 §Phase A](../fabric-p2-realtime-intelligence.md) ·
**Requires:** P1 Phases A–E ✅ (workspace, lakehouse, Gold, Git integration all reused)

## Outcome (done criteria)

- [ ] Eventhouse `eh_energy` exists in `ws-energy-dev`, committed via Git integration.
- [ ] Five Gold SQL queries translated to KQL **by hand** and validated against sample
      data (translations kept in `streaming/kql/drill-sql-to-kql.kql`).
- [ ] 🎓 check passed: Eventhouse vs Lakehouse trade-offs, update policy vs KQL
      materialized view, `bin()`/`summarize` time-window semantics — explainable cold.

## Decisions (made up front — revisit only with a reason)

| Decision | Choice | Why |
|---|---|---|
| Eventhouse layout | One Eventhouse `eh_energy` with its default KQL database (same name) | One item on a 64 CU trial; a single 10-min feed doesn't justify multiple DBs |
| Workspace folder | New folder `streaming` in `ws-energy-dev`; all P2 items (Eventhouse, Eventstream, notebook, queryset, dashboard) live there | Mirrors the P1 `bronze/silver/gold/orchestration` convention; P2 is one more layer, not a new workspace |
| Repo layout | Hand-written artifacts under `streaming/` (`streaming/kql/*.kql`, `streaming/README.md`); Fabric item definitions keep syncing to `/fabric` as usual | Master plan puts P2 in this repo under `streaming/`; Git integration owns `/fabric`, humans own `streaming/` |
| Learning order | KQL drill **before** building anything | Phase C queries and the dashboard are written in KQL; translating known SQL is the fastest transfer path |

## Steps

### A1 `[YOU]` Learn first (~1.5 h, timeboxed)

- [ ] Eventhouse & KQL database concepts — what it is, when it beats a lakehouse
      (append-heavy, time-indexed, seconds-latency reads):
      `https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse`
- [ ] KQL basics — read with the SQL→KQL mapping in mind:
      `https://learn.microsoft.com/kusto/query/tutorials/learn-common-operators`
      and the cheat sheet `https://learn.microsoft.com/kusto/query/sql-cheat-sheet`.
      Focus: `summarize`, `bin()`, `arg_max`/`arg_min`, `join` flavors, `top`,
      `materialized_view()`.
- [ ] Update policies vs KQL materialized views (Phase B's dedup decision hangs on
      this): `https://learn.microsoft.com/kusto/management/materialized-views/materialized-view-overview`
      and `https://learn.microsoft.com/kusto/management/update-policy`.
      Key distinction to retain: an **update policy** transforms rows *per ingestion
      batch* (no memory of earlier batches); a **materialized view** maintains an
      incremental `summarize` *across* batches — cross-batch dedup needs the view.

### A2 `[YOU]` Create the streaming folder + Eventhouse

- [ ] `ws-energy-dev` → toolbar **+ New folder** → `streaming`.
- [ ] Open folder `streaming` → **+ New item** → **Eventhouse** → name `eh_energy`.
      The child KQL database `eh_energy` is created automatically.
- [ ] Open the Eventhouse → confirm the KQL database is there and shows the
      **OneLake availability** toggle on its detail pane (off for now — Phase E flips
      it).
- [ ] Workspace → **Source control** → commit
      (`feat(streaming): add eventhouse for real-time demand`).
- [ ] If the Eventhouse/KQL DB items do **not** appear as committable changes, note it
      under Gotchas (RTI item Git support is newer than lakehouse/notebook support) and
      continue — the `.kql` files in the repo carry the reviewability story regardless.

### A3 `[CLAUDE]` → `[YOU]` SQL→KQL drill (the core of this phase)

- [ ] `[CLAUDE]` Pick five real queries against Gold from Phase C/E work (e.g. monthly
      demand totals, renewables share by month, top-10 price hours, YoY demand delta,
      7-day rolling average price) and write them into
      `streaming/kql/drill-sql-to-kql.kql` as comment blocks: SQL on top, an empty
      `// your KQL here` section under each.
- [ ] `[YOU]` Translate all five **by hand** (no AI, no docs open beyond the cheat
      sheet). Test each against the empty `eh_energy` DB for syntax (use
      `datatable(...)` literals or `print` scaffolding — Claude seeds a small
      `datatable` harness at the top of the file so translations are runnable before
      any real data exists).
- [ ] `[CLAUDE]` Review the translations: correct idiom (e.g. `summarize ... by bin(ts, 1d)`
      instead of date-part gymnastics), flag anti-patterns, commit the final file
      (`docs(streaming): sql-to-kql drill translations`).

### A4 `[CLAUDE]` 🎓 Understanding check — Eventhouse & KQL

- [ ] Quiz Gonzalo (`AskUserQuestion`) on: **Eventhouse vs Lakehouse** (storage layout,
      latency, workload shape — when each wins); **update policy vs materialized
      view** (and which one dedups across ingestion batches); what `bin()` actually
      does to a datetime and why `summarize by bin(ts, 1h)` is the KQL groupby-time
      idiom; `arg_max(ts, *)` semantics.
- [ ] Draw the P2 target topology as a diagram (producer → Eventstream → Eventhouse →
      MV → dashboard/Activator) so Phase B starts with the map in hand.
- [ ] Record weak spots here for the P2 Phase E drills: ______

### A5 `[CLAUDE]` Close the phase

- [ ] Tick done-criteria, set Status ✅, session log. Evidence for this phase is light
      by design (one screenshot: Eventhouse open in the workspace) — the build phases
      carry the screenshots.

## Gotchas & deviations

*(append as encountered — expected suspects: RTI items not all Git-syncable; KQL DB
naming quirks)*

## Session log

- 2026-07-10 — Guide written during repo prep (P2 planning session). Nothing built yet.
