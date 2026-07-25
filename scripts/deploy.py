"""Deploy the Fabric item definitions under `fabric/` into a target workspace.

`fabric-cicd` publishes item definitions from a Git checkout into a Fabric workspace.
This wrapper exists so a deployment is one reviewable command with an explicit
environment argument, rather than an ad-hoc REPL session whose exact arguments are
lost the moment it finishes.

Two authentication paths are selected automatically:

* **Service principal** when `FABRIC_CLIENT_ID`, `FABRIC_CLIENT_SECRET` and
  `FABRIC_TENANT_ID` are all present. This is the enterprise path and the one
  `.github/workflows/deploy-prod.yml` uses.
* **Interactive browser** otherwise. This is the documented fallback for tenants that
  block service-principal registration outright — see `docs/phases/phase-f-cicd.md`
  step F1, where the Track A student tenant returned 401 from the Entra admin centre.

The direction of travel matters and is the whole point of the phase: the **dev**
workspace is bound to Git and is where authoring happens; **prod** is never Git-bound
and never hand-edited, and receives its contents only from this script running against
a reviewed commit.

Example:
    python scripts/deploy.py --environment prod
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Final

from azure.core.credentials import TokenCredential
from azure.identity import ClientSecretCredential, InteractiveBrowserCredential
from fabric_cicd import (
    FabricWorkspace,
    publish_all_items,
    unpublish_all_orphan_items,
)

LOGGER: Final[logging.Logger] = logging.getLogger("deploy")

#: Deploy targets. These are workspace *identifiers*, which is a different job from the
#: GUID substitution in `fabric/parameter.yml`: this decides **where** items are
#: published, parameterization decides **what the published items point at**.
WORKSPACE_IDS: Final[dict[str, str]] = {
    "dev": "476b58fd-19e3-4c0d-bde7-c3f16d2a6fcf",
    "prod": "30ace2e2-4312-491c-831f-f44727888722",
}

#: Every item type this solution actually contains. The list must stay exhaustive:
#: `unpublish_all_orphan_items` only considers types named here, so a type omitted by
#: accident would silently survive in prod after being deleted from the repo.
ITEM_TYPES_IN_SCOPE: Final[list[str]] = [
    "Lakehouse",
    "Environment",
    "Notebook",
    "DataPipeline",
    "VariableLibrary",
    "SemanticModel",
    "Report",
]

#: Repository root is this file's parent's parent; `fabric/` is what Fabric syncs.
REPOSITORY_DIRECTORY: Final[Path] = Path(__file__).resolve().parent.parent / "fabric"


def clean_deploy_directory(directory: Path) -> None:
    """Remove Python bytecode caches from the deploy tree before publishing.

    `fabric-cicd` publishes from the *filesystem*, not from `git`: every file in an
    item's folder is sent as a definition part. A stray `__pycache__/*.pyc` is
    gitignored — invisible to `git status`, never in the repo — yet on disk, so it leaks
    into the item and the Fabric API rejects it ("this item type doesn't support
    definition parts with empty payload"). This bit the first prod deploy: four
    notebooks whose `notebook-content.py` had been imported locally each carried a
    `.pyc` and failed, while the three without one published fine.

    Only `__pycache__` directories are removed — always regenerable, never source — so
    this targeted safeguard cannot touch an item definition.

    Args:
        directory: The repository directory that will be published.
    """
    for cache_dir in directory.rglob("__pycache__"):
        LOGGER.warning("Removing bytecode cache from deploy tree: %s", cache_dir)
        shutil.rmtree(cache_dir, ignore_errors=True)


def build_credential() -> TokenCredential:
    """Select an authentication path from the environment.

    Returns:
        A `ClientSecretCredential` when all three service-principal variables are
        present, otherwise an `InteractiveBrowserCredential`.
    """
    client_id = os.environ.get("FABRIC_CLIENT_ID")
    client_secret = os.environ.get("FABRIC_CLIENT_SECRET")
    tenant_id = os.environ.get("FABRIC_TENANT_ID")

    if client_id and client_secret and tenant_id:
        LOGGER.info("Authenticating as service principal %s", client_id)
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    LOGGER.info(
        "Service-principal variables absent; falling back to interactive browser "
        "login. Expected on tenants that block app registration (phase-f-cicd.md, F1)."
    )
    return InteractiveBrowserCredential()


def deploy(environment: str, *, remove_orphans: bool) -> None:
    """Publish every in-scope item definition into the environment's workspace.

    Args:
        environment: Target environment key; must be a key of `WORKSPACE_IDS`. It is
            also the key `fabric/parameter.yml` matches on, and the name Fabric uses to
            pick the active Variable Library value set — so the three must agree.
        remove_orphans: Whether to delete workspace items that no longer exist in the
            repository. Off by default because it deletes; see `main`.

    Raises:
        KeyError: If `environment` is not a known deploy target.
    """
    workspace_id = WORKSPACE_IDS[environment]
    LOGGER.info(
        "Deploying %s -> environment=%s workspace=%s",
        REPOSITORY_DIRECTORY,
        environment,
        workspace_id,
    )

    clean_deploy_directory(REPOSITORY_DIRECTORY)

    workspace = FabricWorkspace(
        workspace_id=workspace_id,
        environment=environment,
        repository_directory=str(REPOSITORY_DIRECTORY),
        item_type_in_scope=ITEM_TYPES_IN_SCOPE,
        token_credential=build_credential(),
    )

    publish_all_items(workspace)

    if remove_orphans:
        LOGGER.warning(
            "Removing workspace items absent from the repository (--remove-orphans)."
        )
        unpublish_all_orphan_items(workspace)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        The parsed namespace with `environment` and `remove_orphans`.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--environment",
        required=True,
        choices=sorted(WORKSPACE_IDS),
        help="Deploy target. Also selects the parameter.yml and value-set keys.",
    )
    parser.add_argument(
        "--remove-orphans",
        action="store_true",
        help=(
            "Delete items present in the workspace but absent from the repository. "
            "Off by default: it is destructive, and it is only safe while "
            "ITEM_TYPES_IN_SCOPE covers every type the solution uses."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Run a deployment from the command line."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    args = parse_args()
    environment: str = args.environment
    remove_orphans: bool = args.remove_orphans

    deploy(environment, remove_orphans=remove_orphans)
    LOGGER.info("Deployment to %s completed.", environment)


if __name__ == "__main__":
    main()
