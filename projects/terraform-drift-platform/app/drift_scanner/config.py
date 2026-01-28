from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class DriftScannerConfig:
  """Strongly-typed configuration for a drift scan run."""

  environment: str
  account_id: str
  workspace: str
  dynamodb_table: str
  s3_bucket: str
  sns_topic_arn: str
  github_owner: str | None = None
  github_repo: str | None = None

  @classmethod
  def from_env(cls) -> "DriftScannerConfig":
    """Load configuration from environment variables.

    Required:
      DRIFT_ENVIRONMENT
      DRIFT_ACCOUNT_ID
      DRIFT_WORKSPACE
      DRIFT_DDB_TABLE
      DRIFT_S3_BUCKET
      DRIFT_SNS_TOPIC_ARN

    Optional:
      DRIFT_GITHUB_OWNER
      DRIFT_GITHUB_REPO
    """

    def get_required(name: str) -> str:
      value = os.getenv(name)
      if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
      return value

    return cls(
      environment=get_required("DRIFT_ENVIRONMENT"),
      account_id=get_required("DRIFT_ACCOUNT_ID"),
      workspace=get_required("DRIFT_WORKSPACE"),
      dynamodb_table=get_required("DRIFT_DDB_TABLE"),
      s3_bucket=get_required("DRIFT_S3_BUCKET"),
      sns_topic_arn=get_required("DRIFT_SNS_TOPIC_ARN"),
      github_owner=os.getenv("DRIFT_GITHUB_OWNER"),
      github_repo=os.getenv("DRIFT_GITHUB_REPO"),
    )

