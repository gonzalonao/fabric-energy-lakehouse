# Learning log — 🎓 checks, misconceptions, and the drill bank

One of this project's three standing objectives is **Fabric fluency for Gonzalo's job**
(see `CLAUDE.md`). This file is the durable record of that objective. It spans **all
phases and both tracks** — unlike the per-track progress files, which only record what was
*built*.

**For Claude, at every 🎓 checkpoint:**

1. Quiz with `AskUserQuestion` — plausible distractors, no giveaway phrasing. A question is
   only useful if a confident-but-wrong mental model would pick a wrong answer.
2. Log the result in the **Scoreboard**, and any miss in the **Misconception ledger** —
   with the *correction*, not just the fact that it was missed.
3. Add the phase's concepts to the **Drill bank** so they can be re-asked later.
4. **Re-test prior misses** in the next quiz. A gap isn't closed until it's answered
   correctly *after* the correction, on a differently-worded question.

**At Phase G (and again at the end of P2):** run the drill bank cold — out loud, no notes.
Prioritize anything in the Misconception ledger that isn't marked closed, then sweep the
rest. The bar is the P1 plan's interview drills: he should be able to *explain* each
answer, not just recognize it.

---

## Scoreboard

| Date | Check | Track/Phase | Score | Outcome |
|---|---|---|---|---|
| 2026-07-13 | Phase A opener (pre-build) | A / Phase A | 1/3 | 2 misconceptions logged (M1, M2) |
| 2026-07-14 | A11 — Git integration (post-build) | A / Phase A | 3/4 | **M1 + M2 closed**; M3 opened |
| 2026-07-14 | B1.5 — ingestion & watermarks (pre-build) | A / Phase B | 4/6 | M4 + M5 opened. Correct: Copy-vs-Web, watermark-after-success, ForEach sequential, the `Generación total` trap |
| 2026-07-17 | M4 re-test (right after running the B8c kill-test) | A / Phase B | 1/1 | **M4 closed** — rejected "watermark resume" with the original miss on the table |
| 2026-07-18 | C1.5 — Delta, DQ gate & MLVs (pre-build) | A / Phase C | **6/6** | First perfect check. Beat the "automatic" trap twice head-on (V-Order-only; gate-doesn't-auto-retry). No new misconceptions |
| 2026-07-19 | M6 re-test (at C5, before the corrupted-file run) | A / Phase C | 0/1 | **M6 still open — overcorrected**: predicted the shared quarantine appends would fail like B7. The miss moved from "rows are disjoint → safe" to "same table → always fails"; correction = the conflict matrix (see M6). Rejected the "automatic" distractor |
| 2026-07-20 | M5 re-test (at C7, before first endpoint use) | A / Phase C | 1/1 | **M5 closed** — a `DELETE` on the endpoint correctly predicted to fail for the architectural reason (read-only projection; writes go through Spark), rejecting both the async-sync trap and the wrong-layer permissions answer |
| 2026-07-20 | C8 — Phase C post-build (6 scenario questions on the built system) | A / Phase C | 3/6 | ✓ write-then-raise rationale, gold staleness (rejected the "automatic" plant — 2 more kills), the wheel-change process (his own earlier question, retained). ✗ wholetext latency (picked "different code path" over data-indistinguishability), string-value coercion (**M7 opened**), civil-date rationale (credited Direct Lake, a platform non-requirement — the *wrong-mechanism* axis again) |
| 2026-07-20 | Phase D pre-build (M6 + M7 re-tests + 2 concept checks) | A / Phase D | **4/4** | **M6 + M7 both closed.** M6: parallel silver = safe, *different tables* (rejected his B7 overcorrection) AND named sequencing as a capacity choice, not correctness. M7: string value → quarantine (rejected the coercion trap). Also ✓ gate-between-silver-and-gold, ✓ no-semantic-refresh (Direct Lake reads Delta). No new misconceptions |
| 2026-07-21 | E1.5 — Direct Lake vs Import vs DirectQuery (pre-build, the #1 drill) | A / Phase E | **4/4** | ✓ freshness by reframe (no copy), ✓ fallback trigger = SQL view, ✓ "Direct Lake only" = fail-loudly proof, ✓ Import-copy vs DL-transcode. Beat the "automatic" plant twice (auto-refresh distractor on both freshness and Import-vs-DL) and the M2-echo layer-conflation distractor ("schema lakehouse needs DL-only"). Asked for a deeper view-fallback example — engaged, not a gap. No new misconceptions |
| 2026-07-21 | M3 re-test (Phase F opening, against the real `pipeline-content.json`) | A / Phase F | 1/1 | **M3 closed — the last open misconception.** Predicted the *silent* failure (runs green against dev's objects), rejecting the "Fabric remaps GUIDs on Update all" plant and the wrong-layer permissions answer. **Third consecutive check where the "automatic" distractor failed to land.** One factual sub-question left for F6 to settle empirically (see M3) |
| 2026-07-23 | F (mid-phase, while prod backfilled) — CI/CD concepts just built | A / Phase F | 4/6 | ✓ notebook-vs-pipeline parameterization (auto-re-point), ✓ `$items` removes the two-pass (resolves post-create), ✓ orphan-removal coupled to scope completeness, ✓ anonymous-vs-OAuth connection portability. ✗ **two on the wrong-mechanism axis**: thought fabric-cicd *compiles* notebooks (it reads the filesystem verbatim and POSTs files as parts — `M8`), and credited "Git integration unavailable on prod tenant" for prod being release-only (it's a **design choice**; dev+prod share the tenant, so it's available and refused — M3-adjacent). Re-test both at F8 |
| 2026-07-23 | D4 — Phase D post-build (6 scenario questions on the built orchestration) | A / Phase D | **6/6** | **Second perfect check** (after C1.5). ✓ M6 cold *again* — parallel silver safe, *different tables/logs*, sequencing named as a capacity choice; ✓ the alert-funnel mechanism in full (cross-source AND vs same-source OR, terminal-skip + Fail activity); ✓ gate-before-gold protects last-good data; ✓ no-refresh = Direct Lake reframe, not Import; ✓ Fail activity re-asserts red after a succeeding handler flips the run green; ✓ dependency AND/OR logic stated precisely — and Q2+Q6 both correct shows it's a model, not a memorized fact. Beat the "auto-serialize" and "auto-refresh on schedule" plants. No new misconceptions; **zero open misconceptions remain** |

---

## Misconception ledger

The highest-value section: what a confident-but-wrong model predicted, and why it's wrong.
Re-test anything not marked ✅ **closed**.

### M1 — "Fabric Git sync is real-time" ✅ closed (2026-07-14)

**Believed:** editing an item in the workspace propagates to the Git branch automatically.
**Actually:** nothing moves without a human action. Fabric holds changes as *pending* in the
**Source control** panel; you **Commit** to push workspace → Git, and **Update all** to pull
Git → workspace. It is a manual, two-directional, portal-driven sync — *not* a file watcher,
and *not* CI/CD.
**Why it matters:** if you assume auto-sync you will lose work, or believe a teammate can see
a change that only exists in your workspace.

### M2 — "The Lakehouse schemas checkbox enables Direct Lake" ✅ closed (2026-07-14)

**Believed:** ticking *Lakehouse schemas* at creation is what makes Direct Lake work.
**Actually:** it enables **schema namespaces** (so tables can live under `bronze` / `silver` /
`gold` rather than one flat list) and is a **prerequisite for materialized lake views**
(Phase C). It is **irreversible** — it can only be chosen at lakehouse creation.
**Direct Lake is unrelated**: it's a *storage/query mode* for a semantic model that reads
Delta/Parquet files in OneLake directly, with no import refresh and no DirectQuery
round-trip to SQL. A non-schema lakehouse can serve Direct Lake perfectly well.
**Why it matters:** conflating a storage-layout choice with a query-mode choice — two
different layers of the stack.

### M3 — "Prod is populated by binding it to `main` and clicking Update all" ✅ closed (2026-07-21, at Phase F)

**Believed:** deploy to production by setting up Git integration on `ws-energy-prod`
pointing at `main`, then pulling with *Update all*.
**Actually:** the prod workspace is **never Git-bound**. `fabric-cicd` (GitHub Actions,
triggered by a merge to `main`) deploys item definitions *into* it. Four reasons the Git-bind
route is wrong:
1. **No parameterization.** Git integration copies definitions verbatim — dev's lakehouse
   GUIDs, workspace IDs and connection values would land in prod still pointing at dev.
   `fabric-cicd`'s `parameter.yml` exists precisely to substitute per-environment values.
2. **It isn't CI/CD.** It's a human clicking a button — no trigger, no gate, no run log.
   The point of Phase F is that *merging a PR to `main`* deploys.
3. **It makes prod writable.** A Git-bound workspace has a Source control panel — someone
   can hand-edit prod and commit *back* to `main`, reopening the door the decision record
   explicitly closes ("populated exclusively by `fabric-cicd` from `main`; never hand-edit").
4. **Wrong identity.** `fabric-cicd` deploys as a **service principal** from a runner; Git
   integration acts as *you*, interactively.

**The model to hold:**
> **Git integration** = dev workspace ⇄ source control → *authoring*.
> **fabric-cicd** = source control → prod workspace → *release*.
> Different direction, different mechanism, different identity. **Prod never talks to Git.**

**Concrete evidence, now in the repo (2026-07-16).** Reason 1 above stopped being theoretical
the moment B3 committed. `fabric/orchestration/pl_ingest_ree.DataPipeline/pipeline-content.json`
contains two **dev-tenant GUIDs, hardcoded**:

```json
"artifactId": "8bdb6c16-94fa-9379-43ad-836e6cabfc1b",   // dev's lh_energy lakehouse
"connection": "3cc793f5-7a71-4133-8102-f88cadcd4458"     // dev's REST connection
```

Git-bind `ws-energy-prod` to `main`, hit *Update all*, and prod's pipeline would write into the
**dev** lakehouse through the **dev** connection. **It would not error** — the GUIDs resolve
fine, they just resolve to the wrong tenant's objects. That silence is the whole danger: a
misconfiguration that throws is a nuisance; one that succeeds against the wrong target is an
incident. Substituting these two values is precisely what `parameter.yml` is for.

*Contrast worth noticing:* `v_alert_email` is **not** hardcoded here — it's a
`libraryVariables` reference. The variable library is already the parameterization seam for
values we chose to control; `parameter.yml` covers the GUIDs Fabric bakes in whether we like
it or not.

**Re-test at:** Phase F (before building the deploy) and Phase G — **open this file and ask
him to find what breaks.** Far better than re-asking the multiple-choice.

**✅ Closed 2026-07-21, at the opening of Phase F.** Re-tested against the real committed
artifact rather than a multiple-choice abstraction: the two hardcoded GUIDs were put on screen
and the scenario asked was *"bind `ws-energy-prod` to `main`, Update all, run `pl_ingest_ree`
in prod — what happens?"* Distractors included the signature **"Fabric remaps the GUIDs
automatically during Update all"** plant and a wrong-layer permissions answer. Answered
**runs green against dev's objects** — the silent-success model, which is the whole point of
the misconception. Counts as closed: correct, new framing, after the correction, with the
automatic-remap trap explicitly on the table. **This is the third consecutive check where the
"…happens automatically" distractor failed to land** (C1.5 ×2, Phase D pre-build, here) —
the axis that defined M1/M3/M5 now looks genuinely worked through, not just recognized.
One cold pass remains in the Phase G full-bank drill (drill A5).

**⚠️ Open factual question, to be settled empirically at F6 — not a gap in his model.** Two
of our own documents disagree about whether the *lakehouse sink* fails loudly or silently
writes to dev. This entry says it would not error; the tracker's ID table calls
`workspaceId: 00000000-…` a **same-workspace placeholder**, which would mean prod resolves the
sink to *prod workspace + dev artifactId*, finds nothing, and errors. Both cannot be true.
The **connection** half is not in doubt — connections are tenant-level and owned by Gonzalo,
so prod would genuinely reach REE through dev's connection.

M3's verdict is unaffected either way (the identity, gating and prod-writability arguments
each disqualify Git-binding prod on their own), but *silently wrong* vs *loudly broken* is the
moral of the story, so it is worth knowing. **F6's two-pass bootstrap is a free natural
experiment**: the first prod deploy necessarily runs before prod's lakehouse GUID exists to be
substituted. Record the observed behaviour there and correct whichever document is wrong.

### M4 — "The watermark is what makes a re-run safe" ✅ closed (2026-07-17, at B8)

**Believed:** re-running a slice is safe because the watermark stops `pl_ingest_ree` from
re-fetching a window it already has.
**Actually:** two independent mechanisms, two different problems — and they were conflated:

| | Mechanism | Solves | If removed |
|---|---|---|---|
| **Incremental** | watermark (`bronze.ctl_watermark`) | *what* to fetch | slow, still correct |
| **Idempotent** | deterministic path + Copy **overwrite** | what happens if you fetch it **twice** | fast, **corrupt** |

**Two proofs they're separate:**
1. **The kill-test (B8).** Cancel a backfill mid-flight, re-run the same params → identical
   file set. The watermark was *never updated* (we only write it after success), so it
   cannot be what protected the re-run. The deterministic path + overwrite did.
2. **`pl_backfill_ree` never reads the watermark at all** — it fetches `p_from`→`p_to`
   unconditionally. If the watermark were the idempotency mechanism, the backfill would
   have none.

**The model to hold:**
> The **watermark decides what to fetch**. The **path decides what happens when you fetch
> it twice.** Idempotency is a property of the *destination*, not of the *scheduler*.

**Why it matters:** an idempotency guarantee that actually rests on a watermark is a guarantee
that evaporates exactly when you need it — on the failed run, where the watermark didn't move.
**Re-test at:** B8 (the kill-test is the live demonstration) and Phase G.

**✅ Closed 2026-07-17, immediately after running B8c himself.** Re-test question (differently
worded, all four plausible mechanisms offered): *"you cancelled the backfill mid-run, re-ran
identical params, got an identical file set — what made that safe?"* Distractors included the
original miss (*watermark resume*) plus the profile-pattern trap (*Fabric auto-resume*) and a
wrong-layer answer (*Delta rollback* — `Files/` isn't Delta). Answered **deterministic
overwrite**, correctly rejecting the watermark option *after having just watched the cancelled
run die before the watermark chain* — the live proof that the watermark couldn't have been the
protector. Gap counts as closed: correct, on new wording, after the correction, with the
original wrong answer on the table. Still gets one cold pass in the Phase G full-bank drill.

### M5 — "A Lookup can write, and it commits automatically on success" ✅ closed (2026-07-20, at C7)

**Believed:** the Lookup could write the watermark back, but its automatic commit-on-success
would break our after-the-copy timing rule.
**Actually:** wrong on both halves.
1. **A Lookup never writes — ever.** It is a read activity by definition: it runs a query and
   returns rows into the pipeline's run state. There is no write path to commit.
2. **The real reason is architectural, not a timing or permissions detail.** The **SQL
   analytics endpoint over a Lakehouse is read-only** — it's a T-SQL *query surface* projected
   over the Delta files in OneLake. It can read them; it cannot modify them. Every write to a
   Lakehouse Delta table goes through a writer engine (Spark) → hence `nb_update_watermark`.

**The distinction to file:** Lakehouse SQL analytics endpoint = **read-only**. Fabric
**Warehouse** = **read/write via T-SQL**. Same T-SQL surface, different write capability —
this is one of the primary Lakehouse-vs-Warehouse decision criteria.

**Why it matters:** this was the planted "…happens automatically" distractor (see *Observed
pattern*) and it landed — the signature failure, in a new costume.
**Re-test at:** Phase C (when the SQL endpoint is used for the gold proofs) and Phase G.

**✅ Closed 2026-07-20, immediately before first hands-on endpoint use (C7).** Re-test
scenario: *"while in the endpoint you run `DELETE FROM silver.quarantine …` — what happens?"*
Distractors included the async-sync costume of the original miss (*deletes, syncs back on the
next refresh*) and a wrong-layer answer (*works for workspace admins*). Answered **fails — the
endpoint is a read-only projection; writes go through a Spark writer**, i.e. the architectural
reason, not a permissions or timing story. Counts as closed: correct, new wording, after the
correction, original miss on the table. The C7 proofs he ran seconds later are the live
demonstration. One cold pass remains in the Phase G full-bank drill.

---

## Drill bank

Questions to run cold at Phase G / end of project. Grows one section per phase.

### Phase A — Platform & Git

1. Draw the Track A topology from memory: Fabric workspace, Azure DevOps, GitHub, prod.
   Which arrows are manual? Which are automated? Which pair never talk to each other?
2. You edit a notebook in Fabric and close the browser. What does a teammate cloning the
   GitHub repo see, and why?
3. Why does a Fabric notebook serialized as `.py` produce a reviewable PR diff when an
   `.ipynb` does not? (Answer must mention outputs/execution counts/JSON.)
4. What does the *Lakehouse schemas* option do, when can you set it, and what breaks later
   if you skip it?
5. How does `ws-energy-prod` get its contents, and name two things that would go wrong if you
   simply bound it to `main` instead.
6. Why is GitHub the canonical remote on Track A when Fabric only ever syncs with Azure
   DevOps? What keeps the two remotes from diverging?
7. Why does Track B exist at all — what does building the same thing twice actually prove?

### Phase B — Batch ingestion

1. Both a Copy and a Web activity can call the REE API anonymously. Why must ours be Copy?
   (Answer must reach: Web's response stays in the pipeline's run state, size-limited and
   never persisted; our payload must land as a file in Bronze.)
2. **Copy job vs Copy activity** — Microsoft recommends Copy job as the *default* for Bronze
   ingestion, and it has native watermark-based incremental copy, which Copy activity lacks.
   So why did we use Copy activity anyway? (Reach: our unit of work is a *URL*, not a
   queryable table — the date window is baked into the URL string, so there's nothing to
   watermark against; plus we need ForEach + Invoke-pipeline composition. Bonus: what would
   change if the source were a SQL database instead?)
3. Why is the watermark written only after a successful copy? What *specifically* goes wrong
   if written first? (Reach: **silent permanent gap** — the failed window is skipped forever
   and no error surfaces.)
4. Bronze has no dedup logic at all. What makes a re-run safe? (M4 — must separate
   *incremental* from *idempotent*, and explain why the kill-test proves it's not the
   watermark.)
5. Why read the watermark via Lookup on the SQL endpoint but write it via a Spark notebook?
   (M5 — the endpoint is **read-only**; Lookup never writes. How does a Warehouse differ?)
6. Why is `Sequential = ON` on the backfill ForEach a decision rather than an oversight?
7. `estructura-generacion` returns 16 identically-shaped series. What's the trap, why does no
   structural check catch it, and how does the DQ gate turn it into an asset?
8. Draw the three pipelines and their call graph from memory. Which one never reads the
   watermark, and why is that not a bug?

### Phase B — Batch ingestion (cont.): concurrency

9. Three notebook activities each `MERGE` into `bronze.ctl_watermark`, wired in parallel off the
   ForEach. The backfill's data landed 129/129, but the run **failed**. Why, in Delta terms?
   (Reach: optimistic concurrency at Serializable isolation — all read the same version, all try
   to commit the next, one wins, the rest throw `ConcurrentAppendException`.)
10. The run failed yet Bronze was complete and no data was lost or corrupted — only the watermark
    table was left under-claiming. Why is that the *safe* failure mode, and which design rule
    produced it? (Reach: watermark-written-only-after-success + idempotent paths → a failure
    yields re-fetch pressure, never gaps.)
11. Two ways to make three writes to one control table safe. Name them and the trade-off.
    (Reach: serialize the transactions, or batch them into one transaction; parallel blind writes
    to an unpartitioned Delta table are the anti-pattern.)

### Phase C — Transform & DQ

1. You append to a typed Silver table and a parser bug flips a column's type. With default
   Delta settings, what happens — and why is that behavior a *feature* for DQ? (Reach: schema
   enforcement rejects the whole write; a parser regression can't silently poison Silver.)
2. Which of V-Order, OPTIMIZE, VACUUM is automatic on a Fabric Spark write, and which two must
   you run yourself? What does each of the manual two solve? (Reach: V-Order auto = read layout;
   OPTIMIZE manual = small-file compaction; VACUUM manual = deletes dead files, costs time travel.)
3. What does `VACUUM` physically do, what's the default retention, and name two things it can
   break. (Reach: deletes unreferenced Parquet past retention; breaks time travel + in-flight readers.)
4. Why is `.collect()` on a Silver table dangerous, and what are the three safe alternatives?
   (Reach: pulls the whole distributed set to the driver → OOM; use display / limit / Spark aggregations.)
5. Our tables are a few hundred k rows. Should we partition by year? Justify with the ~1 GB rule
   and name the failure mode of doing it anyway. (Reach: no; tiny partitions = small-file problem.)
6. `nb_dq_gate` writes every result to `ops.dq_results` *before* it raises. Why not raise on the
   first failure? (Reach: all failures diagnosable from the table, not just the first in stderr.)
7. MLV vs a notebook-written aggregate — give one case where each is the right call. (Reach: MLV
   for stable relational aggregates you want engine-refreshed with zero maintenance; notebook for
   arbitrary Python, custom schedules, or where MLV preview limits bite.)
8. Schema enforcement vs schema evolution — which is default, and how do you opt into the other?
   (Reach: enforcement default; `mergeSchema` to add columns, `overwriteSchema` for full rebuilds.)
9. Three notebooks run in parallel: each MERGEs its own silver table, all append to one shared
   quarantine table. Safe or not, and why? (M6 — reach: the conflict matrix. MERGE reads → its
   snapshot can be invalidated; a blind append reads nothing → append+append never conflicts;
   different tables = different Delta logs. B7 failed because it was MERGE×3 on *one* table.)
10. A demand value of `-4200` and a value of `null` arrive in the same Bronze file. One lands in
    `silver.quarantine`, the other lands in `silver.demand_daily` and later kills the DQ gate.
    Which is which, and why is that split deliberate? (Reach: structural vs semantic — a null
    can't even become a typed row (quarantine, run continues); a negative parses fine and only a
    *policy* can judge it (gate, run fails). Two failure modes, two mechanisms, two audit trails.)
11. The value arrives as the STRING `"712345.6"` — `float()` would happily convert it. Where
    does it go and why? (M7 — reach: quarantine; coercion is a *choice* and this parser chose
    strict, because a stringly-typed number is producer contract drift worth surfacing, not
    repairing silently.)
12. The wholetext bug shipped in C4 and ran green over 43 files, three times. Why did it stay
    invisible, and what's the general lesson? (Reach: single-line JsonSink files make line-mode
    and wholetext reads indistinguishable — the code's correctness rested on the *producer's
    formatting habit*, an implicit contract; latent until the first multi-line file. Bonus
    mechanism: `.option("wholetext", True)` is clobbered by `text()`'s own `wholetext=False`
    keyword default.)
13. `fact_price_hourly` carries both `datetime_utc` and a Madrid civil `date`. Why can't either
    replace the other? (Reach: UTC = unique row identity across DST; civil date = what daily
    joins mean — `to_date(utc)` misdates the first 1–2 h of every Madrid day onto the previous
    day. Platform requirements — Direct Lake — have nothing to do with it.)
14. Fresh data lands in silver at 08:00. What do `gold.fact_generation_daily` and the MLV each
    show at 08:05, and what has to happen for each to update? (Reach: both stale — the fact
    until `nb_gold_build` reruns, the MLV until its managed refresh; nothing in gold tracks
    silver live, which is why Phase D's master pipeline chains the layers explicitly.)

### Phase D — Orchestration

1. The master chains the three silver notebooks sequentially. If they ran in parallel off the
   Invoke, would they hit `ConcurrentAppendException`? Why or why not — and what *is* the reason
   they're sequential? (M6 — different tables ⇒ different Delta logs ⇒ no conflict; sequential is
   Spark-session/CU contention on 64 CU, a capacity choice, correctness-neutral.)
2. Why does the DQ gate sit *between* silver and gold, not after gold? (Gate needs typed silver
   rows to exist; placing it before gold stops a semantic failure before it's summed into
   facts/MLVs/report — Gold keeps its last-good data.)
3. The pipeline ends at `nb_gold_mlv` with no "refresh semantic model" step. Why is that correct,
   not an omission? (Direct Lake reads the gold Delta directly — no import copy to refresh; a
   refresh step would be an Import-mode reflex.)
4. The first alert wiring — seven `On fail` arrows into one Outlook activity — never fires. Why,
   and what's the fix? (Cross-source deps are AND'd ⇒ all seven must be `Failed` at once, impossible
   in a short-circuiting chain. Fix: single-source funnel on the terminal's `Failed`+`Skipped`
   (same source ⇒ OR) + a `Fail` activity, because a *succeeding* failure-handler flips the pipeline
   to `Succeeded`.)

### Phase E — Serving (Direct Lake)

1. Contrast Import / DirectQuery / Direct Lake by *where the data lives* and *how VertiPaq is fed*.
   Which mode gives freshness AND speed, and by what mechanism? (Direct Lake — transcodes Delta
   Parquet columns on demand from OneLake + framing; no import copy, no per-visual SQL.)
2. Gold is overwritten at 08:05; the report is opened at 08:10 with no refresh — does it show the
   new data, and why? (Yes — reframe repoints the model at the new Parquet files; no copy exists to
   refresh.)
3. Name three things that trigger a Direct Lake → DirectQuery fallback. (A SQL-endpoint *view*
   (no Parquet to transcode); unsupported DAX/model features; capacity guardrail row limits.)
4. Why "Direct Lake only" over the default "Automatic"? (Fail loudly — a query that can't be served
   directly errors instead of silently downgrading, so a rendered report *proves* no fallback.)
5. You base a model table on a SQL-endpoint view instead of the Delta table. Under "Direct Lake
   only", what happens and why? (Errors — the view has no Parquet files; Direct Lake can't transcode
   a saved query, so it would need DirectQuery, which "only" mode forbids.)
6. Fabric auto-made a default semantic model over `lh_energy`. Why build a separate `sm_energy`?
   (Default = uncurated convenience over every table; the deliverable is a curated gold-only model
   with designed relationships and DAX measures.)

### Phase F — CI/CD (`fabric-cicd`)

1. `parameter.yml` rewrites lakehouse/workspace GUIDs for **notebooks** but has no pipeline
   entry, though both reference the lakehouse. Why don't pipelines need one? (fabric-cicd
   auto-re-points activities referencing *same-workspace* items to the target's equivalents;
   notebooks pin a literal `default_lakehouse` + `default_lakehouse_workspace_id` it doesn't
   touch. "Workspace IDs never need substitution" is true for pipelines, false for notebooks.)
2. The guide assumed a two-pass bootstrap. Why did `$items.Lakehouse.lh_energy.$id` remove it?
   (It resolves to the target item's GUID *after* that item is created in the deploy — the value
   needn't exist in advance.)
3. `__pycache__/*.pyc` is gitignored and not in the repo, yet it broke the prod deploy. How?
   (**M8** — fabric-cicd reads the *filesystem*, not git, and POSTs every file in an item's
   folder as a definition part; it does **not** compile anything. The stray `.pyc` shipped
   verbatim and the API rejected it. Lesson: a deploy inherits untracked cruft from the working
   tree — "not in git ≠ won't deploy".)
4. The anonymous REST connection worked in prod at once; the Outlook connection needed
   re-authentication. General rule? (Anonymous connections carry no credentials → portable
   across a deploy; OAuth/credentialed ones need re-authorization per environment — the consent
   doesn't travel with the item definition. An unauthenticated connection makes Fabric reject
   the pipeline at *submission* with a fast BadRequest.)
5. `unpublish_all_orphan_items` is opt-in. Beyond "it deletes", why dangerous, and what makes it
   safe here? (It only acts on types in `ITEM_TYPES_IN_SCOPE`; narrow the scope for a partial
   deploy and still run it, and it deletes in-scope prod items absent from the partial release.
   Safe here: off by default + the type list is exhaustive.)
6. Prod is never Git-bound. Two mechanisms, and why prod uses only one? (Git integration =
   bidirectional *authoring*, dev ⇄ `develop`; fabric-cicd = one-way *release*, `main` → prod.
   Prod stays release-only **by design, not because Git integration is unavailable** — on
   Track A dev+prod share the tenant, so it *is* available and deliberately refused: for
   parameterization, gating, non-hand-editability, and controlled deploy identity.)
7. The deploy failed 4 of 7 notebooks but published 3. What single fact explains *which* failed?
   (Only the 4 with a local `__pycache__` — see Q3. The 3 without one published fine; the split
   was diagnostic.)
8. Nobody configured a schedule in `ws-energy-prod`, yet `pl_daily_refresh` ran by itself at
   08:00 the morning after the deploy. How? And why is this *stronger* evidence for the CI/CD
   claim than the manual run was? (Reach: Fabric serializes a pipeline's schedule into Git as a
   dedicated `.schedules` file — own JSON schema, `localTimeZoneId` — so it is part of the item
   definition and `fabric-cicd` publishes it like any other part. Prod inherited an **active
   trigger** from `main`. It's stronger evidence because deployment reproduced the
   *operational behaviour*, not just the item graph: prod is self-operating, which is only
   possible when it's built from source control instead of clicked together. Corollary hazard:
   a deployed schedule starts consuming capacity in prod immediately, whether or not you meant
   it to.)

### Phase G — Capacity & cost (G3)

*Seeded 2026-07-23 from the live Capacity Metrics observation during the prod backfill — a
teaching moment, not a scored check. The full concept write-up is in
[`capacity-notes.md`](capacity-notes.md).*

1. A heavy ~4-hour background backfill (Spark + pipeline) runs on a 64-CU capacity. Would it
   show as a utilization **spike** in the Capacity Metrics app? Why or why not? (Reach: no —
   **background operations are smoothed over a 24-hour window**; interactive over 5 minutes.
   Fabric amortizes a background job's CU-seconds across 24h, so a heavy-but-short batch shows
   as a low sustained baseline, not a spike — by design, to keep bursty batch work from
   tripping throttling. A flat utilization line is the correct reading, not a capture failure.)
2. Fabric bills compute in **CU-seconds**. Why is this pipeline "long in wall-clock but light
   in CU", and why is that not a contradiction? (Reach: the backfill is **network/latency-bound**
   — 129 *sequential* HTTP fetches behind REE's Imperva WAF — not compute-bound. Wall-clock time
   spent waiting on rate-limited I/O consumes almost no CU; duration ≠ cost.)
3. The trial is **FTL64** (64 CU) and a full day smoothed to <2%. What's the smallest paid SKU
   that would comfortably run this workload, and what's the argument? (Reach: an **F2** = 2 CU;
   even a whole day's CU-seconds is a fraction of an F2's daily budget at this cadence — the
   *trial* SKU size is what Microsoft grants, not what the workload *needs*. Don't confuse the
   two.)
4. "No throttling / no overages" on the Throttling tab — what does it prove, and what does it
   *not*? (Reach: proves the smoothed load stayed inside the CU envelope with no carryforward
   penalty; does **not** prove the job is cheap in absolute CU-seconds — 24h smoothing can hide
   a genuinely large consumer under the daily average right up until it exceeds capacity. Read
   the itemized CU(s), not just the utilization %, to judge cost.)

## Misconception ledger (cont.)

### M6 — "Independent parallel writes to one Delta table are fine" ⬜ open (2026-07-17)

**Believed (implicit in the build):** three activities each updating a different *row* of
`bronze.ctl_watermark` can run in parallel safely — they touch different data.
**Actually:** Delta's unit of concurrency is the **file/commit, not the row**. An unpartitioned
table is one root; three concurrent `MERGE`s all read version N and race to commit version N+1.
One wins; the losers throw **`ConcurrentAppendException`** ("Files were added to the root of the
table by a concurrent update"). Row-level disjointness doesn't help unless Delta can *prove* it —
which needs a partition predicate the MERGE didn't have.
**Fix (chosen):** serialize the three writes (sequential transactions never conflict). Alternative:
one transaction that upserts all rows. Retry is a band-aid, not a fix.
**Not the usual axis.** Gonzalo's other misses cluster on "assumes the platform automates a manual
step"; this one is different — a genuine distributed-systems/isolation gap, not a Fabric-seam
assumption. His Delta instincts are strong on *storage* (V-Order, schema, time travel) but this is
*concurrency*, a distinct sub-area worth a second look at Phase C (silver writes) and Phase D
(orchestration, where parallel branches multiply).
**Re-test at:** Phase C and Phase G.

**Re-test 2026-07-19 (C5): still open — the miss inverted.** Scenario: three parallel
`nb_bronze_to_silver` runs, each MERGEing its *own* silver table but all appending to the shared
`silver.quarantine`. He predicted a B7-style `ConcurrentAppendException` on the quarantine
appends — an **overcorrection**: from "different rows → safe" (original) to "same table →
always fails" (now). Both miss the actual rule, the **conflict matrix**:

> A conflict needs **the same table AND at least one writer that also *read* it.**
> - **MERGE reads first** (its commit declares the snapshot version it read); a concurrent
>   commit invalidates that snapshot → `ConcurrentAppendException`. B7 = 3 MERGEs, 1 table.
> - **A blind append reads nothing** — no snapshot to invalidate. Concurrent appends to one
>   table all succeed (N+1, N+2, N+3). Append+append is the always-safe concurrent pair.
> - MERGEs into *different* tables are different Delta logs — no interaction at all.

So the parallel ×3 scenario is safe by construction — and `silver.quarantine` being
**append-only** is precisely what makes sharing it across writers safe. Positive note: he
rejected the "Fabric serializes them automatically" distractor.
**Re-test at:** Phase D (parallel orchestration branches make it concrete) and Phase G.

**✅ Closed 2026-07-20 (Phase D pre-build).** Re-test scenario, grounded in the real
`pl_daily_refresh` build: *"the three `nb_bronze_to_silver` runs are chained sequentially —
if you rewired them to run in parallel off the Invoke, would they hit
`ConcurrentAppendException`?"* Distractors offered both prior wrong models (the B7
overcorrection "parallel writes conflict" and the "shared silver schema → one log" variant).
Answered **no — different tables, different Delta logs**, and unprompted named the sequential
choice as a **capacity** decision (Spark session contention on 64 CU), not a correctness one.
That's the full conflict matrix applied cleanly: same-table-AND-a-reader is the trigger, and
three different tables can't interact. Counts as closed — correct, new wording, after both the
correction *and* the earlier overcorrection, with the wrong models on the table. One cold pass
remains in the Phase G full-bank drill (drill #9).

### M7 — "The typed parser coerces what it plausibly can" ✅ closed (2026-07-20, at C8→D)

**Believed:** a demand value arriving as the *string* `"712345.6"` parses into
`silver.demand_daily` — the parser coerces numeric-looking strings.
**Actually:** `_as_float` is deliberately strict — `isinstance(value, (int, float))` or
`TypeError`; a string quarantines even though `float("712345.6")` would succeed. **Coercion is
a choice, and this codebase chose against it:** a number arriving as a string means the
producer's contract drifted, and silent coercion would hide that drift until it broke
something subtler. Strict rejection converts contract drift into a visible quarantine row
with a reason, on day one.
**The boundary to hold:** *anything that cannot become a typed row without guessing* is
**structural** → quarantine (run continues). Only values that ARE valid typed rows get judged
**semantically** → gate (run fails). A string value never reaches the gate's jurisdiction.
**Related pattern:** the Q5 miss the same day credited a platform requirement (Direct Lake)
for a domain decision (civil-date joins) — the *wrong-mechanism* axis (see M4, Observed
pattern). Not ledgered separately; covered by drill re-asks.
**Re-test at:** Phase D and Phase G.

**✅ Closed 2026-07-20 (Phase D pre-build), one day after opening.** Re-test scenario, new
value and framing: *"REE starts sending `value: \"637873.15\"` as a JSON string — what happens
to that record in `nb_bronze_to_silver`?"* Distractors: the original coercion miss ("`float()`
succeeds → reaches Silver") and a wrong severity ("crashes the run"). Answered **quarantined**,
holding the boundary that the parser refuses to coerce because a stringly-typed number is
producer contract drift worth surfacing. Correct, new wording, after the correction, original
miss on the table → closed. One cold pass remains at Phase G (drill #11). *Note the Q5
civil-date/Direct-Lake wrong-mechanism slip was also re-tested this session (concept Q4, "why
no semantic-model refresh") and answered correctly — Direct Lake reads Delta directly.*

### M8 — "fabric-cicd transforms/compiles the items it deploys" ⬜ open (2026-07-23, Phase F)

**Believed:** the `__pycache__/*.pyc` deploy failure happened because fabric-cicd *compiled*
the notebooks during deploy and the compilation failed.
**Actually:** fabric-cicd performs **no transformation of any kind**. It reads the
`repository_directory` **from the filesystem** (not from `git`) and POSTs every file in an
item's folder to the Fabric API as a *definition part*, byte-for-byte. The `.pyc` was already
on disk from an earlier local import of `notebook-content.py`; the deploy shipped it verbatim
as a notebook part and the API rejected it ("this item type doesn't support definition parts
with empty payload"). No compile step exists to fail.
**Why it matters:** the whole operational lesson — *"not in git ≠ won't deploy"* — depends on
seeing that the tool reads **disk**, not the repo, and publishes whatever is sitting there.
Crediting a transform step hides that: the real hazard is that a deploy inherits untracked
cruft from the working tree. Fix shipped: `deploy.py` strips `__pycache__` before publishing.
**Axis:** *crediting the wrong mechanism* (see M4's second axis / the Observed-pattern note) —
same family as the same-session Q6 slip ("prod uses fabric-cicd because Git integration is
unavailable" — actually a *design choice*; dev+prod share the Track A tenant, so it's
available and refused). Not ledgered separately; covered by the F8 re-ask.
**Re-test at:** F8 (Phase F post-build) and Phase G.

*(Phase C–G sections appended at each 🎓 checkpoint.)*

---

## Observed pattern — target future quizzes here

Gonzalo's misses cluster on a single axis: **assuming the platform automates something that
Fabric actually requires an explicit, human or pipeline-driven step for** (M1: sync assumed
real-time; M3: prod assumed to self-populate; **M5: a read-only Lookup assumed to write, and to
commit on its own**). His Delta/Spark/data-modeling instincts are solid; the gap is in Fabric's
*operational seams* — where the magic stops and a deliberate action is required.

**So:** when quizzing on a new Fabric feature, always include a distractor of the form
"…happens automatically." That is the misconception most likely to be live. **It landed again
at B1.5 (M5)** — the pattern is stable and worth planting every time.

**Update (C1.5, 2026-07-18): the trap was planted twice and beaten both times** — he correctly
picked V-Order as the *only* automatic write step (rejecting "all three") and rejected the
"gate auto-retries failed checks" distractor. First time the signature miss didn't land. Not
evidence the axis is closed (it's a recognition test, not a cold recall, and M5's *live*
re-test — the read-only SQL endpoint — is still pending at C7); keep planting. But worth noting
the Delta-storage sub-area specifically is now solid under adversarial phrasing.

**A second, related axis emerged at B1.5 (M4): crediting the wrong mechanism.** He knows both
mechanisms exist and what each does, but attributes the guarantee to the more *visible* one
(the watermark) rather than the one actually providing it (path + overwrite). Distinct from the
"automatic" axis — nothing is assumed automatic here; the causality is just wired to the wrong
component. **So also ask "what breaks if you remove X?"** — the counterfactual is what
separates a real mental model from a plausible story, and it's how M4 was exposed.
