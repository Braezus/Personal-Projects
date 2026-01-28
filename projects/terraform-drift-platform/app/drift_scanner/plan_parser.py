from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import DriftAction, DriftChange, ScanContext


def load_plan_json(plan_json_path: Path) -> Dict[str, Any]:
  """Load the JSON produced by `terraform show -json`."""
  return json.loads(plan_json_path.read_text())


def _actions_from_change(change: Dict[str, Any]) -> List[DriftAction]:
  raw_actions = change.get("change", {}).get("actions", [])
  actions: List[DriftAction] = []
  for a in raw_actions:
    try:
      actions.append(DriftAction(a))
    except ValueError:
      # Unknown action type from Terraform – keep as-is but mark as UPDATE
      actions.append(DriftAction.UPDATE)
  return actions


def _summary_before_after(change: Dict[str, Any]) -> Dict[str, Any]:
  """Return a summarized subset of before/after attributes.

  We intentionally avoid including the full object to keep audit and
  notifications readable. Implementations can extend this to include
  more or less data as appropriate.
  """
  before = change.get("change", {}).get("before", {}) or {}
  after = change.get("change", {}).get("after", {}) or {}

  # Shallow copy; a real implementation might filter by allowlist.
  return {"before": before, "after": after}


def parse_drift_changes(
  ctx: ScanContext, plan_json: Dict[str, Any]
) -> List[DriftChange]:
  """Convert a Terraform plan JSON into DriftChange objects."""
  changes: List[DriftChange] = []

  resource_changes = plan_json.get("resource_changes", []) or []
  for rc in resource_changes:
    address = rc.get("address", "")
    rtype = rc.get("type", "")
    actions = _actions_from_change(rc)
    if not actions:
      continue

    summary = _summary_before_after(rc)
    changes.append(
      DriftChange(
        environment=ctx.environment,
        account_id=ctx.account_id,
        workspace=ctx.workspace,
        resource_address=address,
        resource_type=rtype,
        actions=actions,
        before=summary["before"],
        after=summary["after"],
      )
    )

  return changes

