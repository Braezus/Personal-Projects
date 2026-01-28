from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3

from .models import DriftFinding

logger = logging.getLogger(__name__)


class AuditWriter:
  """Writes drift findings to DynamoDB and S3."""

  def __init__(self, table_name: str, bucket_name: str) -> None:
    self._table = boto3.resource("dynamodb").Table(table_name)
    self._s3 = boto3.client("s3")
    self._bucket = bucket_name

  def write_finding(self, finding: DriftFinding) -> str:
    """Write a single finding to DynamoDB and S3.

    Returns the S3 key of the detailed report.
    """
    record = finding.to_audit_record()
    partition_key = f"{record['environment']}#{record['account_id']}"
    sort_key = f"{record['detected_at']}#{record['id']}"

    # DynamoDB summary record
    item = {
      "pk": partition_key,
      "sk": sort_key,
      **record,
    }
    self._table.put_item(Item=item)

    # S3 detailed report
    key = (
      f"env={record['environment']}/"
      f"account={record['account_id']}/"
      f"drift/{record['detected_at']}_{record['id']}.json"
    )

    self._s3.put_object(
      Bucket=self._bucket,
      Key=key,
      Body=json.dumps(record, indent=2).encode("utf-8"),
      ContentType="application/json",
    )

    logger.info(
      "audit_write_success",
      extra={"dynamodb_pk": partition_key, "dynamodb_sk": sort_key, "s3_key": key},
    )

    return key

  def write_findings_batch(self, findings: List[DriftFinding]) -> List[str]:
    keys: List[str] = []
    for f in findings:
      keys.append(self.write_finding(f))
    return keys

