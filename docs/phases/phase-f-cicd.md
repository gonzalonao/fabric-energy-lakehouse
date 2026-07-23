# Phase F — CI/CD (`fabric-cicd`, dev → prod)

**Progress:** tracked per run in [track-a-progress.md](track-a-progress.md) · [track-b-progress.md](track-b-progress.md)
**Days:** D6–D7 · **Plan:** [P1 §Phase F](../fabric-p1-energy-lakehouse.md) ·
**Requires:** Phases A–E ✅ (everything committed on `develop`)

## Outcome (done criteria)

- `develop` → `main` gated by PR (branch protection on `main`; Gonzalo approves —
      review-gate rule).
- A merge to `main` (or the documented local fallback run) reproduces the full
      solution in `ws-energy-prod` **untouched by hand**.
- Dev-vs-prod values resolved via Variable Library / `parameter.yml`, not edits.
- The enterprise SPN pattern documented in README even if the tenant blocks it.

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

Four gates; stop at the first that closes and record which.

1. **Registration.** `portal.azure.com` → Microsoft Entra ID → **App registrations** →
   **New registration** (`spn-fabric-cicd`, single tenant, no redirect URI).
2. **Credential.** Overview → copy *Application (client) ID* + *Directory (tenant) ID* →
   **Certificates & secrets** → new client secret. ⚠️ The secret's **Value** is shown once
   and never again; it goes into GitHub Actions secrets by hand, **never into the repo and
   never pasted into chat**.
3. **Tenant switch.** `app.fabric.microsoft.com` → ⚙ → **Admin portal** → Tenant settings →
   *Service principals can use Fabric APIs*. No **Admin portal** entry = you are not a
   tenant admin, so you can neither read nor change it.
4. **Workspace access.** `ws-energy-prod` → Manage access → Add → the SPN as **Admin**.
   If it never appears in the picker, the switch is off.

**Outcome `[Track A]` — 2026-07-21: ☒ blocked, at gate 1, wholesale.**
`portal.azure.com` → Microsoft Entra ID returns **HTTP 401 "You don't have access"** on the
blade itself, and the direct App-registrations deep link
(`#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade`) 401s identically. So this is not
the narrower *"Users can register applications = No"* toggle — the student tenant sets
**"Restrict access to Microsoft Entra admin center = Yes"**, closing the whole directory
administration surface to non-admins. App registration was never reachable to be denied.
Gates 2–4 are therefore untestable, not untested. **Fallback confirmed** — F6 runs
`scripts/deploy.py` locally with `InteractiveBrowserCredential`.

**Expectation `[Track B]`** — own tenant, so Gonzalo *is* the tenant admin: all four gates
should pass, and Track B is where the SPN + GitHub Actions path gets demonstrated for real.
That contrast is the point of running the phases twice; record Track B's outcome in the same
format so the two sit side by side.

> **Why this is worth 30 minutes even when it fails:** the README can then name the exact
> directory policy that prevented the enterprise path, rather than implying the pattern was
> skipped for convenience. A blocked probe that is documented precisely reads as engineering
> judgement; an undocumented gap reads as a missing feature.

### F2 `[YOU]` Collect IDs + prod value set

- Prod workspace ID: open `ws-energy-prod` → copy the GUID from the URL.
      Dev workspace ID: same. Dev `lh_energy` ID: from the lakehouse URL. Paste all
      three to Claude.
- `vl_energy` → add a **prod value set** (alert email same; any dev-only values
      overridden). Commit.

### F3 `[CLAUDE]` Deploy code

- Branch `feature/cicd`. Write:
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
- `ruff` + `mypy --strict` green; PR → merge to `develop`.

### F4 `[YOU]` Branch protection

- GitHub → repo → Settings → Branches → protect `main`: require a pull request
      before merging, require 1 approval. (Your approval = the develop→main review
      gate from the workspace rules.)

### F5 `[CLAUDE]` + `[YOU]` The gated promotion

- `[CLAUDE]` Open PR `develop` → `main`: title `release: P1 lakehouse v1.0.0`,
      body = summary of phases A–E + evidence links. **Wait for your approval — never
      auto-merge this one.**
- `[YOU]` Review + merge.

### F6 `[YOU]` + `[CLAUDE]` Deploy to prod

- SPN path: `[YOU]` add the three secrets in GitHub → Actions fires on the merge →
      watch the run.
- Fallback path: `[CLAUDE]` runs `python scripts/deploy.py --environment prod`
      from `main` locally; `[YOU]` complete the browser login prompt when it appears.
- First-deploy bootstrap: after items appear in prod, `[YOU]` grab the prod
      `lh_energy` GUID → `[CLAUDE]` completes `parameter.yml` → **re-run the deploy**
      (now fully parameterized) → this second run is the one that counts.

### F7 `[YOU]` Verify prod (money screenshots)

- `ws-energy-prod` contains: lakehouse, all notebooks, all pipelines, `sm_energy`,
      `rpt_energy`, `vl_energy` — item-by-item screenshot next to dev.
- Spot-open a notebook and a pipeline: parameters point at **prod** GUIDs (the
      find-replace worked) — screenshot one example.
- Evening (off-peak): run `pl_backfill_ree` in prod; next day run
      `pl_daily_refresh` in prod manually once → green. Open `rpt_energy` in prod →
      renders with prod data.
- Nothing was hand-created in prod at any point. If something was → note it in
      Gotchas and redo that item via deploy.

### F8 `[CLAUDE]` Wrap-up

- Evidence into `docs/evidence/phase-f/`; record F1 outcome + deploy timings in
      session log; tick done-criteria, Status ✅.
- Tag the release on `main`: `git tag -a v1.0.0 -m "P1 energy lakehouse"` + push
      the tag (semver rule).
- 🎓 **Understanding check:** Claude confirms Gonzalo can explain the release model —
      **Git integration (dev workspace ↔ `develop`)** vs **fabric-cicd (`main` → prod,
      never Git-bound, never hand-edited)**, how `parameter.yml` swaps dev→prod GUIDs, and
      **why the SPN path is the enterprise default** (and what blocked it here). This maps
      directly to the "Git integration + fabric-cicd → enterprise release flow" drill.

## Gotchas & deviations

### 2026-07-21 `[Track A]` — the SPN block is wider than "app registration is off"

The Day-0 risk register predicted the *"Service principals can use Fabric APIs"* tenant
setting would be the blocker. The real blocker sits one layer earlier and is broader: the
**Entra admin centre itself** is unreachable (401 on the blade and on the App-registrations
deep link), so the Fabric-side setting was never the binding constraint.

Two consequences worth stating precisely, because they are different claims:

- **We cannot demonstrate the SPN path on this tenant** — not "we chose not to".
- **We also cannot report the state of the Fabric SPN setting**, because reading it needs the
  Admin portal we can't open. The honest README sentence is *"unverifiable on this tenant"*,
  not *"disabled"*.

`.github/workflows/deploy-prod.yml` still ships (pipeline-as-code is the evidence either way),
gated `if: vars.SPN_ENABLED == 'true'` so it exists without firing. Track B, on Gonzalo's own
tenant, is where it actually runs.

### To settle at F6 — does a wrong lakehouse GUID fail loudly or silently?

The two-pass bootstrap gives a free natural experiment: the **first** prod deploy necessarily
runs before prod's `lh_energy` GUID exists to substitute, so `parameter.yml` still carries
dev's. Two of our documents disagree about what happens — the learning log (M3) says the
pipeline resolves dev's lakehouse and silently writes there; this repo's ID table calls
`workspaceId: 00000000-…` a *same-workspace* placeholder, which would instead make prod look
for dev's artifact ID inside prod and error.

**Record what actually happens and correct whichever document is wrong.** The connection half
is not in doubt: connections are tenant-level and owned by Gonzalo, so prod genuinely reaches
REE through dev's connection either way.

*(Other expected suspects, still open: fabric-cicd item-type support gaps for preview items —
Variable Library / MLV handling; `InteractiveBrowserCredential` and MFA.)*

## Session log

*Moved to the per-track trackers ([A](track-a-progress.md) / [B](track-b-progress.md)) — phase-specific gotchas stay above.*
