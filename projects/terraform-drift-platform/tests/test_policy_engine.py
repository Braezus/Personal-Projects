from __future__ import annotations

from pathlib import Path

from projects.terraform-drift-platform.app.drift_scanner.models import (
  DriftAction,
  DriftChange,
)
from projects.terraform-drift-platform.app.drift_scanner.policy_engine import (
  evaluate_policies,
  load_policies,
)


def make_change(resource_type: str, environment: str) -> DriftChange:
  return DriftChange(
    environment=environment,
    account_id="000000000000",
    workspace="default",
    resource_address=f"{resource_type}.example",
    resource_type=resource_type,
    actions=[DriftAction.UPDATE],
    before={"tags": {"env": environment}},
    after={"tags": {"env": environment, "extra": "x"}},
  )


def test_policy_engine_uses_specific_rule(tmp_path: Path) -> None:
  policies_path = (
    Path(__file__).resolve()
    .parents[1]
    / "policies"
    / "drift_policies.yml"
  )
  policy_set = load_policies(policies_path)

  change = make_change("aws_iam_role", "prod")
  decision = evaluate_policies(policy_set, change)

  assert decision.rule_name == "prod_iam_role_drift"
  assert decision.severity.value in {"HIGH", "CRITICAL"}

