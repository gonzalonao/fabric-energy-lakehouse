# Build log

How this lakehouse was built, in the order it happened — and, more usefully, what went wrong
along the way and what each failure forced. The architecture is described in the
[README](../README.md); the reasoning behind each choice is in
[`decisions.md`](decisions.md); the inventory of what exists after each phase, with links to
the evidence, is in [`phases.md`](phases.md). This file is the narrative that connects them.

Every incident below is real and most produced a design change. They are recorded because a
platform that never surprised anyone during construction is usually one that hasn't been
pushed hard enough to find out.

---

## Platform and source control

Two workspaces on a Fabric trial capacity, and a lakehouse created with **schemas enabled** —
an irreversible choice made at creation, because schema namespaces (`bronze` / `silver` /
`gold` rather than one flat table list) are also a prerequisite for materialized lake views
later.

**The first obstacle was the tenant, not the tooling.** Fabric's GitHub Git provider was
blocked outright on the student tenant this was built on. Rather than abandon source control,
the build pivoted to **Azure DevOps** as Fabric's provider while keeping **GitHub canonical**,
with both remotes kept in lockstep by mirroring — a discipline verified after every commit:

```bash
git rev-list --left-right --count origin/develop...devops/develop   # must be 0 0
```

Bidirectional integration was then proven end to end rather than assumed: a notebook was
edited in Fabric, committed from the workspace, changed again through a pull request on
GitHub, and pulled back into Fabric with *Update all*. Notebooks serialize as `.py` with cell
markers, so that pull request produced a **one-line reviewable diff** — the reason `.py` is
worth insisting on over `.ipynb`, whose JSON, outputs and execution counts make review
theatre.

## Ingestion

All three REE endpoints were probed live **before** any pipeline was built. Three facts came
out of that and shaped everything downstream: the API answers anonymously, it caps a request
at a **one-month window** (hence chunking), and a planned ESIOS-token dependency turned out to
be unnecessary — real-time price data is available tokenless, so the token was dropped from
the design entirely.

Ingestion uses a Copy **activity** rather than Fabric's recommended Copy **job**, deliberately:
the unit of work here is a **URL**, not a queryable table, so Copy job's headline
watermark-based incremental feature has nothing to watermark against.

Three things the documentation didn't warn about, all found by inspecting what Fabric actually
produced:

- **The Mapping tab must stay empty.** Populate it and Copy reshapes the payload; Bronze must
  land the response byte-faithfully. Verified by comparing the raw response against the landed
  file.
- **Fabric pre-populates an RFC 5988 pagination rule.** It would concatenate `Link`-header
  pages into a single file. REE sends no `Link` header, so it is inert — but that was
  confirmed by probing, not assumed.
- **The source sits behind an Imperva WAF.** That turned `Sequential = ON` on the backfill loop
  from politeness into self-preservation.

### The backfill failed, and the failure was the point

The full history load landed **129 of 129 files correctly** — and the pipeline run still
reported **Failed**. Three watermark `MERGE` statements had been wired to run in parallel, one
per indicator, into a single unpartitioned Delta table. Delta's unit of concurrency is the
commit, not the row: all three read the same version and raced to commit the next, so one won
and the rest threw `ConcurrentAppendException`. The fix was to serialize them; the alternative
— blind retry — would have been a band-aid over a design error.

What made this a *safe* failure is a rule set much earlier: **the watermark is written only
after a successful copy.** A failure therefore leaves re-fetch pressure, never a silent gap.

### Proving idempotency isn't the watermark

"Incremental" and "idempotent" are routinely conflated. They were treated here as two
problems with two mechanisms — a watermark decides *what to fetch*, a deterministic path plus
Copy-overwrite decides *what happens if you fetch it twice* — and the split was then proven
rather than asserted:

- A backfill was **cancelled mid-flight** and re-run with identical parameters. The file set
  came back identical while the watermark had never moved, so the watermark cannot have been
  what protected the re-run.
- The backfill pipeline **never reads the watermark at all**. If idempotency depended on it,
  the backfill would have none.

A separate test regressed the watermarks by two weeks; a single daily run self-healed them.

## Transform and data quality

All parsing and data-quality logic lives in a typed Python package (`mypy --strict`, Ruff,
**26 pytest tests over real captured API responses**) shipped as a wheel into a Fabric
Environment. It is deliberately **Spark-free at import**, so the whole suite runs locally with
no cluster. Notebooks stay thin orchestration.

Data quality is split across two jurisdictions, which is the single most load-bearing idea in
this layer:

| Problem | Example | Mechanism | Run outcome |
|---|---|---|---|
| **Structural** — cannot become a typed row without guessing | a `null` where a number is required; a numeric value arriving as a string | **quarantine** | continues |
| **Semantic** — parses fine, violates policy | negative demand | **DQ gate** | **fails** |

The gate writes *every* result to `ops.dq_results` **before** it raises, so a failed run is
diagnosable from a table rather than from the first line of stderr.

### The gate immediately found something real

Its first run flagged **8 negative generation rows** — all coal. They were not corrupt: they
were legitimate thermal self-consumption, a plant drawing more than it generated. The rule was
wrong, not the data, so the bound became renewable-aware and shipped as a new wheel version.
Paying that cost in the open is the trade-off of putting DQ policy in tested code rather than
in a notebook cell.

### A latent bug found by a test that was looking for something else

A deliberately corrupted file was injected to prove the fail → fix → green arc. It did that —
and also exposed a reader bug that had been running green over 43 files, three times.

The reader passed `wholetext=True`, which was silently overridden by the `text()` API's own
keyword default. The bug stayed invisible because every file the pipeline had ever produced
was single-line JSON, making line-mode and whole-text reads indistinguishable. **The code's
correctness had been resting on the producer's formatting habit** — an implicit contract that
would have broken on the first multi-line response.

Gold is a full atomic rebuild each run — no incremental merge — joined on **natural keys**,
with two aggregates declared as materialized lake views instead. Three SQL scripts run against
the lakehouse endpoint verify the star schema independently of the pipeline that built it, one
of which reproduces a monthly renewables share three separate ways.

## Orchestration

One master pipeline chains the whole medallion from a single daily trigger: ingest → three
silver notebooks → DQ gate → gold rebuild → MLV declaration. That last step *declares* the
materialized lake views rather than refreshing them — `CREATE … IF NOT EXISTS` makes it an
idempotent no-op once they exist, and the engine owns their refresh. The corollary is that
editing an MLV's SQL alone changes nothing; a definition change needs an explicit drop first.

**The first failure-alert design could never have fired.** It wired seven `On fail` arrows
from seven activities into a single email activity. In Data Factory, dependencies from
*different* sources are **AND**-ed — so all seven activities would have had to fail
simultaneously, which is impossible in a chain that short-circuits on the first failure. The
alert was silent by construction.

The corrected design routes off the **terminal** activity on `Failed` **or** `Skipped`
(conditions from the *same* source are OR-ed), so it fires exactly once on any failure
anywhere in the chain. That exposed a second trap: **a failure handler that succeeds flips the
whole run to `Succeeded`**, so a `Fail` activity was added to re-assert the red status. Both
behaviours were then proven with a controlled break — one email, gold correctly skipped, run
honestly red.

## Serving

The semantic model is **Direct Lake on OneLake**, chosen over Direct Lake on SQL because it
reads Delta straight from OneLake with no SQL-endpoint metadata lag and — decisively — **has
no DirectQuery fallback path at all**. The "no fallback" requirement is satisfied by
construction rather than by a toggle.

Two consequences followed. Direct Lake supports **no calculated columns**, so every derived
column belongs in Spark. And Power BI's auto date/time had been silently enabled with no
web-modeling UI to turn it off — it was disabled by editing the model definition directly,
which is only possible because the model is source-controlled as TMDL.

### The report's problems were model problems

The first rendered report showed a year-on-year figure of 40.5% and a monthly trend that dived
at the right-hand edge. Both looked like formatting issues and neither was:

- The **YoY measure had no opinion on whether its two windows were comparable**, so an
  unfiltered card compared two periods holding different amounts of loaded data. It was
  replaced with a self-contained rolling-12-complete-months comparison anchored to the last
  loaded date.
- The **trend counted the current, partial month**. A completeness guard now blanks any month
  whose last calendar day is later than the data actually loaded, and a freshness measure
  reports the earliest last-loaded date across all three facts — the earliest, because a
  maximum would hide one lagging indicator behind two current ones.

Fixing them in the model rather than the report mattered: measures live in Git, so the fix
travelled with the definition instead of being re-done in every consumer. A report that looks
wrong is not automatically a formatting problem.

### A guard that depended on something nobody had declared

The completeness guard asked one question — *does this bucket's last calendar day fall after
the last day of loaded data?* — and answered it by reading the maximum date visible in the
calendar dimension. Inside a month bucket that maximum **was** the month's last calendar day,
so the test worked, and the measure's own comment recorded that as a fact.

It was not a fact. It was true only because the calendar was hardcoded to run years past the
data, which made every bucket's last row a real calendar day rather than a data boundary. When
the calendar's bounds were later derived from the facts — a change made for unrelated reasons,
to stop empty future years leaking into slicers and rolling averages — the final month's last
calendar row became the last *loaded* day. The test compared that day to itself, concluded the
month was complete, and the partial month reappeared in the trend.

Nothing broke loudly. The gold table was correct, the measure was unchanged, and the report
rendered. The defect lived in the seam: a measure had taken a dependency on a property of a
table in another layer, and neither side recorded it. The fix computes the month's calendar
end (`EOMONTH`) instead of inferring it from how far the calendar happens to run, so the
question the measure asks no longer depends on how the calendar was built. The same guard was
then extended to the generation trend, which had never had one — and deliberately **not** to
the renewables-share trend, because a ratio over a partial month is a valid number while a sum
over one is a misleading dip.

Two habits came out of it: a comment asserting *X is Y* deserves a second look at whether it
means *X happens to equal Y right now*, and a change that makes a table more correct in
isolation can still break a consumer that was relying on the older, sloppier shape.

### The number that was wrong for a month, and the identity check behind it

Looking at the repaired trend turned up something worse. The renewables share sat around
55% for every month of the loaded history and then dropped to **27%** for July — a step, on
the first of the month, holding flat for twenty-six days. Weather does not do that.

It was almost exactly a halving, which points at the denominator rather than the numerator.
REE's generation payload carries a `Generación total` series alongside the technologies: the
sum of them, not one of them. It was being parsed as a technology, adding a second copy of
the day's total generation to the denominator and leaving renewables untouched. Confirmed two
ways — the composite's monthly figure matched the sum of the fifteen technologies to within
6 MWh in 22.5 million, and generation divided by demand, an independently ingested indicator,
stepped from 1.13 to 2.29 on the same date.

The exclusion had been there from the start:

```python
if attributes.get("composite") is True:
```

`is True` is an identity comparison against Python's `True` singleton, not a truth test. It
excluded the aggregate only while the payload decoded to a JSON boolean; `"true"`, `1` and a
missing attribute all passed straight through, and `1 is True` evaluates to `False`.

The reason it surfaced in one month and not the others is the more useful half of the story.
Closed months are ingested once and their raw files never touched again. The current month is
re-fetched and overwritten **in full every morning** by the incremental path. So a change in
the upstream payload propagates only into the file still being rewritten, and the defect
appears at what looks like a calendar boundary but is really a *fetch-date* boundary. The
corollary is worth sitting with: the historical data is correct because nothing has re-read
it, not because anything verified it. Re-running the backfill would have broken those months
too.

Three things had to be true at once for this to reach a report. The parser had a flaw. Every
SQL proof and every evidence screenshot sampled a historical month, so none of them could
have caught a defect that only affects freshly fetched data. And the DQ gate passed 20/20,
because all twenty rules ask whether an individual value is sane — non-null, in range,
correctly signed — and a composite row is entirely sane in isolation. Nothing asked whether
the rows *added up*.

The fix accepts the flag in any encoding and falls back to matching the title, with a
regression test per encoding. More importantly the gate gained `ratio_band`, its first check
that compares two tables rather than judging one in isolation: daily generation over daily
demand, bounded to `[0.8, 1.6]`. The observed history sits at 1.10–1.17; the defect ran at
2.29. A check that had existed for one afternoon would have turned a month of quietly wrong
reporting into a failed pipeline run on day one.

## Release

The production workspace is **never Git-bound and never hand-edited**. It is built exclusively
by `fabric-cicd` from `main`, driven by a typed deploy script and a parameter file that
rewrites per-environment bindings.

The service-principal path was attempted first and **blocked at the tenant**: the Entra admin
centre returns HTTP 401 on both the blade and the app-registration deep link, so registration
was unreachable rather than merely denied. The enterprise workflow ships in the repo anyway,
gated behind a repository variable, and production is deployed by running the same script
locally with an interactive login — same code, same commit, different identity and trigger.

Two findings simplified the design before it shipped: parameter references to a target item
resolve **after** that item is created, which removed an assumed two-pass bootstrap entirely;
and pipelines re-point same-workspace references automatically, so only items that embed a
binding in free text need parameterizing.

### Two defects that only running it could find

- **Bytecode caches broke the first deploy.** `fabric-cicd` publishes from the **filesystem**,
  not from git, POSTing every file in an item's folder as a definition part. Gitignored
  `__pycache__` files — invisible to `git status`, absent from the repo — shipped as notebook
  parts and the API rejected four of seven notebooks. *"Not in git" does not mean "won't
  deploy."* The deploy script now strips them before publishing.
- **The semantic model silently kept its dev binding.** Direct Lake on OneLake stores its
  source as a Power Query expression holding a literal
  `onelake.dfs.../<workspace>/<lakehouse>` URL, which the deploy tool's automatic re-pointing
  cannot reach into — it re-points *structured* item references, not GUIDs embedded in
  free-text payloads. Production rendered **development's data, looking perfectly healthy**,
  until the binding itself was read.

The second is worth generalizing. Every verification step that passed — all items present,
notebook bindings correct, pipeline sink correct, report renders — is a check that can only
fail **loudly**. None could detect a wrong-but-valid target. Verification thoroughness is not
how many checks pass; it is whether any of them could have failed for the reason that actually
matters.

### Production turned out to be self-operating

The morning after the deploy, the daily pipeline **ran on its own at 08:00**, unattended, with
nobody having configured a trigger. Fabric serializes a pipeline's schedule into Git as a
dedicated file, so it deploys as part of the item definition and production inherited an
active schedule from `main`. Deployment had reproduced the *operational behaviour*, not just
the item graph — something only possible when an environment is built from source control
rather than clicked together.

### A squash merge sent its bill three days late

The first promotion to `main` was squash-merged. The content was identical either way, so it
was accepted as cosmetic. It wasn't: a squash creates a commit with **no ancestry** to the
branch it came from, so `main`'s only common ancestor with `develop` became the repository's
initial scaffold commit.

The next release therefore opened with **six conflicts in files nobody had touched on `main`**
— Git was 3-way-merging every file against a pre-project version and reading both sides as
having independently *added* it. Nothing had actually diverged: `main`'s tree was
byte-identical to `develop`'s at the squashed commit. It was resolved by merging `main` back
into `develop` first, taking `develop`'s tree wholesale, and verifying the merge changed no
content — a merge that existed purely to restore a usable merge base.

**A squash's cost isn't paid at merge time; it's deferred to the next merge.**

---

## What's next

- A **Real-Time Intelligence** extension — Eventstream → Eventhouse/KQL → Activator alerting —
  as a streaming counterpart to this batch platform.
- The same build repeated on **native GitHub Git integration** with a working service-principal
  CI/CD path, on a tenant without the restrictions this one hit, to contrast the two providers
  directly. A blocked path documented honestly on one track is worth more than a blocked path
  quietly omitted from both.
