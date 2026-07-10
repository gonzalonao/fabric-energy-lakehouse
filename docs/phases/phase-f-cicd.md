# Phase F — CI/CD (`fabric-cicd`, dev → prod)

**Status:** ⬜ not started
**Days:** D6–D7 · **Plan:** [P1 §Phase F](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phases A–E ✅ (everything committed on `develop`)

## Outcome (done criteria)

- [ ] `develop` → `main` gated by PR (branch protection on `main`; Gonzalo approves —
      review-gate rule).
- [ ] A merge to `main` (or the documented local fallback run) reproduces the full
      solution in `ws-energy-prod` **untouched by hand**.
- [ ] Dev-vs-prod values resolved via Variable Library / `parameter.yml`, not edits.
- [ ] The enterprise SPN pattern documented in README even if the tenant blocks it.

## Decisions (made up front)

| Decision | Choice | Why |
|---|---|---|
| Deploy tool | `fabric-cicd` 1.2.0 (pinned at D0, Python 3.12) — `FabricWorkspace.publish_all_items()` from the repo's `fabric/` folder | The plan's chosen lib; deploys item definitions from Git, no workspace-to-workspace magic |
| Auth reality | **Expect the SPN path to be blocked**: "Service principals can use Fabric APIs" is a tenant setting and there's no tenant admin (Day-0 finding). Timebox the attempt to 30 min, then take the documented fallback: same script run locally with interactive user auth | The README then shows both: what enterprises do (SPN + GitHub Actions) and what this tenant allowed — honesty reads senior |
| Workflow file | `.github/workflows/deploy-prod.yml` written and committed **even if SPN is blocked** (`workflow_dispatch` trigger, secrets documented) | The pipeline-as-code is portfolio evidence either way |
| Dev/prod values | `parameter.yml` (fabric-cicd find-replace): dev workspace/lakehouse GUIDs → prod GUIDs; `vl_energy` active value set per environment | The standard fabric-cicd mechanism; pairs with the Variable Library from Phase B |
| Prod data | After first deploy, run `pl_backfill_ree` **in prod** once (sequential, off-peak evening) — prod must prove it works, not just exist | Deployed-but-empty isn't "reproduces the solution"; watch the shared 64 CU |
| Prod Git | `ws-energy-prod` is **never** bound to Git and never hand-edited | Deploys only via the script — that's the whole claim |

## Steps

### F1 `[YOU]` SPN attempt (timebox: 30 min, then move on)

- [ ] `portal.azure.com` → Microsoft Entra ID → **App registrations** → try
      **New registration** (`spn-fabric-cicd`).
- [ ] If registration itself is blocked → fallback confirmed, skip to F2.
- [ ] If it works: create a client secret, then try to give the SPN access:
      `ws-energy-prod` → Manage access → Add → the SPN as **Admin**. If the SPN can't
      be added / API calls 401 later, the tenant switch is off → fallback.
- [ ] Record the outcome here (this paragraph becomes README material):
      **Outcome:** ☐ SPN works ☐ blocked at: ______

### F2 `[YOU]` Collect IDs + prod value set

- [ ] Prod workspace ID: open `ws-energy-prod` → copy the GUID from the URL.
      Dev workspace ID: same. Dev `lh_energy` ID: from the lakehouse URL. Paste all
      three to Claude.
- [ ] `vl_energy` → add a **prod value set** (alert email same; any dev-only values
      overridden). Commit.

### F3 `[CLAUDE]` Deploy code

- [ ] Branch `feature/cicd`. Write:
  - `scripts/deploy.py` — typed CLI (`--environment dev|prod`): builds
    `FabricWorkspace(workspace_id, repository_directory="fabric", item_type_in_scope=[...])`,
    `publish_all_items()` + `unpublish_all_orphan_items()`; auth via
    `azure-identity` — `ClientSecretCredential` when SPN env vars present, else
    `InteractiveBrowserCredential` (the fallback).
  - `fabric/parameter.yml` — find-replace: dev workspace GUID → prod, dev `lh_energy`
    GUID → prod (prod lakehouse GUID gets added after first deploy creates it — note
    the two-pass bootstrap in the script's docstring), `vl_energy` active value set.
  - `.github/workflows/deploy-prod.yml` — `workflow_dispatch` + `push: main`;
    pinned Python 3.12; secrets `FABRIC_CLIENT_ID/SECRET/TENANT_ID` documented in a
    README snippet; job marked `if: vars.SPN_ENABLED == 'true'` so it exists but
    doesn't fire while SPN is blocked.
  - README section "CI/CD": both paths, honestly labeled.
- [ ] `ruff` + `mypy --strict` green; PR → merge to `develop`.

### F4 `[YOU]` Branch protection

- [ ] GitHub → repo → Settings → Branches → protect `main`: require a pull request
      before merging, require 1 approval. (Your approval = the develop→main review
      gate from the workspace rules.)

### F5 `[CLAUDE]` + `[YOU]` The gated promotion

- [ ] `[CLAUDE]` Open PR `develop` → `main`: title `release: P1 lakehouse v1.0.0`,
      body = summary of phases A–E + evidence links. **Wait for your approval — never
      auto-merge this one.**
- [ ] `[YOU]` Review + merge.

### F6 `[YOU]` + `[CLAUDE]` Deploy to prod

- [ ] SPN path: `[YOU]` add the three secrets in GitHub → Actions fires on the merge →
      watch the run.
- [ ] Fallback path: `[CLAUDE]` runs `python scripts/deploy.py --environment prod`
      from `main` locally; `[YOU]` complete the browser login prompt when it appears.
- [ ] First-deploy bootstrap: after items appear in prod, `[YOU]` grab the prod
      `lh_energy` GUID → `[CLAUDE]` completes `parameter.yml` → **re-run the deploy**
      (now fully parameterized) → this second run is the one that counts.

### F7 `[YOU]` Verify prod (money screenshots)

- [ ] `ws-energy-prod` contains: lakehouse, all notebooks, all pipelines, `sm_energy`,
      `rpt_energy`, `vl_energy` — item-by-item screenshot next to dev.
- [ ] Spot-open a notebook and a pipeline: parameters point at **prod** GUIDs (the
      find-replace worked) — screenshot one example.
- [ ] Evening (off-peak): run `pl_backfill_ree` in prod; next day run
      `pl_daily_refresh` in prod manually once → green. Open `rpt_energy` in prod →
      renders with prod data.
- [ ] Nothing was hand-created in prod at any point. If something was → note it in
      Gotchas and redo that item via deploy.

### F8 `[CLAUDE]` Wrap-up

- [ ] Evidence into `docs/evidence/phase-f/`; record F1 outcome + deploy timings in
      session log; tick done-criteria, Status ✅.
- [ ] Tag the release on `main`: `git tag -a v1.0.0 -m "P1 energy lakehouse"` + push
      the tag (semver rule).
- [ ] 🎓 **Understanding check:** Claude confirms Gonzalo can explain the release model —
      **Git integration (dev workspace ↔ `develop`)** vs **fabric-cicd (`main` → prod,
      never Git-bound, never hand-edited)**, how `parameter.yml` swaps dev→prod GUIDs, and
      **why the SPN path is the enterprise default** (and what blocked it here). This maps
      directly to the "Git integration + fabric-cicd → enterprise release flow" drill.

## Gotchas & deviations

*(expected suspects: fabric-cicd item-type support gaps for preview items — Variable
Library/MLV handling; two-pass parameter bootstrap; InteractiveBrowserCredential and
MFA)*

## Session log

*(one dated line per session)*
