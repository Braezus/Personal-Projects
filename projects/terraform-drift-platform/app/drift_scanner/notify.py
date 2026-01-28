from __future__ import annotations

import json
import logging
from typing import List

import boto3

from .models import DriftFinding

logger = logging.getLogger(__name__)


class Notifier:
  """Sends drift notifications via SNS."""

  def __init__(self, topic_arn: str) -> None:
    self._sns = boto3.client("sns")
    self._topic_arn = topic_arn

  def publish_findings(self, findings: List[DriftFinding]) -> None:
    if not findings:
      return

    payload = {
      "summary": {
        "count": len(findings),
        "by_severity": {},
        "environment": findings[0].change.environment,
        "account_id": findings[0].change.account_id,
      },
      "findings": [f.to_audit_record() for f in findings],
    }

    # Aggregate severity counts
    for f in findings:
      sev = f.decision.severity.value
      payload["summary"]["by_severity"].setdefault(sev, 0)
      payload["summary"]["by_severity"][sev] += 1

    message = json.dumps(payload, separators=(",", ":"))

    self._sns.publish(
      TopicArn=self._topic_arn,
      Message=message,
      Subject="Terraform Drift Detected",
    )

    logger.info(
      "sns_notify_success",
      extra={
        "topic_arn": self._topic_arn,
        "count": payload["summary"]["count"],
        "by_severity": payload["summary"]["by_severity"],
      },
    )

