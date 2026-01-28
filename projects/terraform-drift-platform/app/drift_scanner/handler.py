from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List

from . import audit as audit_module
from . import config as config_module
from . import notify as notify_module
from . import plan_parser, policy_engine, terraform_runner
from .models import DriftFinding, DriftChange, ScanContext


logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def _scan_once(terraform_dir: Path, cfg: config_module.DriftScannerConfig) -> Dict[str, Any]:
  plan_path = terraform_dir / "tfplan"
  plan_json_path = terraform_dir / "tfplan.json"

  ctx = ScanContext(
    environment=cfg.environment,
    account_id=cfg.account_id,
    workspace=cfg.workspace,
    terraform_dir=str(terraform_dir),
    plan_path=str(plan_path),
    plan_json_path=str(plan_json_path),
  )

  exit_code, stdout, stderr = terraform_runner.run_terraform_plan(
    terraform_dir, plan_path
  )

  logger.info(
    "terraform_plan_completed",
    extra={
      "exit_code": exit_code,
      "environment": cfg.environment,
      "account_id": cfg.account_id,
    },
  )

  if exit_code == 0:
    return {"status": "NO_DRIFT", "findings": []}
  if exit_code == 1:
    logger.error("terraform_plan_failed", extra={"stderr": stderr})
    raise terraform_runner.TerraformError("terraform plan failed")
  if exit_code != 2:
    logger.error("unexpected_exit_code", extra={"exit_code": exit_code})
    raise terraform_runner.TerraformError(f"unexpected terraform exit code: {exit_code}")

  # Drift detected
  terraform_runner.export_plan_json(terraform_dir, plan_path, plan_json_path)
  plan_json = plan_parser.load_plan_json(plan_json_path)

  ctx_obj = ScanContext(
    environment=cfg.environment,
    account_id=cfg.account_id,
    workspace=cfg.workspace,
    terraform_dir=str(terraform_dir),
    plan_path=str(plan_path),
    plan_json_path=str(plan_json_path),
  )

  drift_changes: List[DriftChange] = plan_parser.parse_drift_changes(
    ctx_obj, plan_json
  )

  policies = policy_engine.load_policies(
    Path(__file__).resolve().parents[2] / "policies" / "drift_policies.yml"
  )

  findings: List[DriftFinding] = []
  for change in drift_changes:
    decision = policy_engine.evaluate_policies(policies, change)
    finding = DriftFinding(
      id=str(uuid.uuid4()),
      change=change,
      decision=decision,
    )
    findings.append(finding)

  auditor = audit_module.AuditWriter(
    table_name=cfg.dynamodb_table, bucket_name=cfg.s3_bucket
  )
  s3_keys = auditor.write_findings_batch(findings)

  notifier = notify_module.Notifier(topic_arn=cfg.sns_topic_arn)
  notifier.publish_findings(findings)

  return {
    "status": "DRIFT_DETECTED",
    "count": len(findings),
    "s3_keys": s3_keys,
  }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
  """AWS Lambda entrypoint."""
  cfg = config_module.DriftScannerConfig.from_env()
  terraform_dir = Path(
    event.get("terraform_dir", "/var/task/terraform/envs/dev")
  )
  return _scan_once(terraform_dir, cfg)


def main(argv: List[str] | None = None) -> int:
  """CLI entrypoint for local runs.

  Example:
    python handler.py --env-path ../../terraform/envs/dev
  """
  parser = argparse.ArgumentParser(description="Run a drift scan locally.")
  parser.add_argument(
    "--env-path",
    required=True,
    help="Path to a Terraform environment directory (where main.tf lives).",
  )
  args = parser.parse_args(argv)

  os.environ.setdefault("DRIFT_ENVIRONMENT", "dev")
  os.environ.setdefault("DRIFT_ACCOUNT_ID", "000000000000")
  os.environ.setdefault("DRIFT_WORKSPACE", "default")
  os.environ.setdefault("DRIFT_DDB_TABLE", "drift-audit-dev")
  os.environ.setdefault("DRIFT_S3_BUCKET", "drift-reports-dev")
  os.environ.setdefault("DRIFT_SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:000000000000:drift-topic-dev")

  cfg = config_module.DriftScannerConfig.from_env()
  terraform_dir = Path(args.env_path).resolve()
  result = _scan_once(terraform_dir, cfg)
  print(json.dumps(result, indent=2))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

