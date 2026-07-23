# Execution tracks — two Git-integration variants

The project delivers the **same P1 phases and the same end product twice**, once per
Fabric Git provider. Purpose: portfolio evidence that both integration models are
understood hands-on, plus a real comparison of their trade-offs.

| | **Track A — Azure DevOps** | **Track B — GitHub** |
|---|---|---|
| Progress record | [track-a-progress.md](track-a-progress.md) | [track-b-progress.md](track-b-progress.md) |
| Status | 🔄 **active** (started 2026-07-13) | ⬜ planned (kickoff gate in its tracker) |
| Tenant | Institution (ESESA/UCAM) student tenant | Own Entra tenant (Azure free account) |
| Capacity | Fabric trial capacity | **Paid F2** funded by the Azure $200/30-day credit — paused when idle; subscription auto-disables at credit end (no charge without explicit PAYG upgrade) |
| Fabric Git sync | Workspace ↔ **Azure DevOps** repo, branch `develop`, folder `/fabric` | Workspace ↔ **GitHub** (this repo), branch `develop`, folder `/fabric` |
| Why this provider | GitHub provider is disabled on the tenant (no tenant admin — see phase-a Gotchas 2026-07-13) | Native target; needs own tenant to enable the provider |
| Phase F CI/CD | SPN expected blocked → documented fallback: local `fabric-cicd` run, user auth; GitHub Actions workflow committed but gated off | Real SPN + GitHub Actions deploy |
| Known risks | Institution may restrict DevOps org creation; account revocable; trial window | 30-day credit clock; Power BI Pro licensing on a fresh tenant unverified (Phase E risk); pause discipline required |

## Track A remote layout (git mirroring)

**GitHub stays the canonical repo** — code review, PRs, portfolio visibility all happen
here. Azure DevOps is the operational remote Fabric syncs with.

- Local remotes: `origin` = GitHub, `devops` = Azure DevOps.
- **Fabric commits** land on DevOps `develop` → Claude pulls `devops/develop`, pushes to
  `origin` (GitHub mirror stays complete).
- **Code/docs commits and PR merges** happen on GitHub → Claude pushes `develop` to
  `devops` **before** any *Source control → Update all* in Fabric.
- Rule of thumb: sync both remotes at session start and session end; never let them
  diverge across a Fabric commit.

## Track B kickoff (open questions — resolve when Track A closes)

- Same repo: reuse `/fabric` on a dedicated branch pair, or a `fabric-github/` folder?
  (Item GUIDs will differ between tenants; decide when rebinding.)
- Power BI Pro license path on the fresh tenant (individual trial may be blocked —
  probe first, before spending credit).
- Expected to be much faster than Track A: all code/docs exist; portal work only.

## Mirror rule (vital)

The phase guides in this folder serve **both tracks**:

- Track-agnostic steps are written **once** — they apply to A and B identically.
- Where tracks diverge, steps carry **`[Track A]` / `[Track B]` variant blocks side by
  side in the same file**.
- **Any edit that touches one track's variant must review and, if needed, update the
  sibling variant in the same commit.** Never let the two variants describe different
  end products.
