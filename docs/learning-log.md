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

### M3 — "Prod is populated by binding it to `main` and clicking Update all" ⬜ open

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

**Re-test at:** Phase F (before building the deploy) and Phase G.

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

*(Phase B–G sections appended at each 🎓 checkpoint.)*

---

## Observed pattern — target future quizzes here

Gonzalo's misses cluster on a single axis: **assuming the platform automates something that
Fabric actually requires an explicit, human or pipeline-driven step for** (M1: sync assumed
real-time; M3: prod assumed to self-populate). His Delta/Spark/data-modeling instincts are
solid; the gap is in Fabric's *operational seams* — where the magic stops and a deliberate
action is required.

**So:** when quizzing on a new Fabric feature, always include a distractor of the form
"…happens automatically." That is the misconception most likely to be live.
