from __future__ import annotations

from pathlib import Path

from projects.terraform-drift-platform.app.drift_scanner.models import DriftAction, ScanContext
from projects.terraform-drift-platform.app.drift_scanner.plan_parser import parse_drift_changes


def test_parse_drift_changes_basic(tmp_path: Path) -> None:
  # Minimal synthetic plan JSON structure
  plan = {
    "resource_changes": [
      {
        "address": "aws_s3_bucket.example",
        "type": "aws_s3_bucket",
        "change": {
          "actions": ["update"],
          "before": {"versioning": {"enabled": False}},
          "after": {"versioning": {"enabled": True}},
        },
      }
    ]
  }

  ctx = ScanContext(
    environment="dev",
    account_id="000000000000",
    workspace="default",
    terraform_dir=str(tmp_path),
    plan_path=str(tmp_path / "tfplan"),
    plan_json_path=str(tmp_path / "tfplan.json"),
  )

  changes = parse_drift_changes(ctx, plan)
  assert len(changes) == 1
  c = changes[0]
  assert c.resource_address == "aws_s3_bucket.example"
  assert c.resource_type == "aws_s3_bucket"
  assert DriftAction.UPDATE in c.actions
  assert c.before["versioning"]["enabled"] is False
  assert c.after["versioning"]["enabled"] is True

