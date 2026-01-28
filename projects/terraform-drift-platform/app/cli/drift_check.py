from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from drift_scanner import handler as scanner_handler


def main(argv: List[str] | None = None) -> int:
  parser = argparse.ArgumentParser(
    description="Run a drift check for a given Terraform environment."
  )
  parser.add_argument(
    "--env-path",
    required=True,
    help="Path to the Terraform environment directory.",
  )
  args = parser.parse_args(argv)

  os.environ.setdefault("DRIFT_ENVIRONMENT", "dev")
  os.environ.setdefault("DRIFT_ACCOUNT_ID", "000000000000")
  os.environ.setdefault("DRIFT_WORKSPACE", "default")
  os.environ.setdefault("DRIFT_DDB_TABLE", "drift-audit-dev")
  os.environ.setdefault("DRIFT_S3_BUCKET", "drift-reports-dev")
  os.environ.setdefault("DRIFT_SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:000000000000:drift-topic-dev")

  event: Dict[str, Any] = {"terraform_dir": str(Path(args.env_path).resolve())}
  result = scanner_handler.lambda_handler(event, context=None)
  print(json.dumps(result, indent=2))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())

