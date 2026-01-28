from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class DriftAction(str, Enum):
  CREATE = "create"
  UPDATE = "update"
  DELETE = "delete"
  REPLACE = "replace"


class Severity(str, Enum):
  LOW = "LOW"
  MEDIUM = "MEDIUM"
  HIGH = "HIGH"
  CRITICAL = "CRITICAL"


class Category(str, Enum):
  SECURITY = "SECURITY"
  AVAILABILITY = "AVAILABILITY"
  COST = "COST"
  OTHER = "OTHER"


class Recommendation(str, Enum):
  IGNORE = "IGNORE"
  REVIEW = "REVIEW"
  AUTO_REMEDIATE = "AUTO_REMEDIATE"


@dataclass
class DriftChange:
  """Represents a single resource-level drift item derived from a Terraform plan."""

  environment: str
  account_id: str
  workspace: str
  resource_address: str
  resource_type: str
  actions: List[DriftAction]
  before: Dict[str, Any]
  after: Dict[str, Any]


@dataclass
class PolicyDecision:
  """Result of applying policies to a DriftChange."""

  severity: Severity
  category: Category
  recommendation: Recommendation
  rule_name: Optional[str] = None
  notes: Optional[str] = None


@dataclass
class DriftFinding:
  """A DriftChange enriched with policy decisions and metadata."""

  id: str
  change: DriftChange
  decision: PolicyDecision
  detected_at: datetime = field(
    default_factory=lambda: datetime.now(timezone.utc)
  )

  def to_audit_record(self) -> Dict[str, Any]:
    """Return a compact dict suitable for DynamoDB and JSON logging."""
    return {
      "id": self.id,
      "environment": self.change.environment,
      "account_id": self.change.account_id,
      "workspace": self.change.workspace,
      "resource_address": self.change.resource_address,
      "resource_type": self.change.resource_type,
      "actions": [a.value for a in self.change.actions],
      "severity": self.decision.severity.value,
      "category": self.decision.category.value,
      "recommendation": self.decision.recommendation.value,
      "rule_name": self.decision.rule_name,
      "detected_at": self.detected_at.isoformat(),
    }


@dataclass
class ScanContext:
  """Context for a drift scan invocation."""

  environment: str
  account_id: str
  workspace: str
  terraform_dir: str
  plan_path: str
  plan_json_path: str

