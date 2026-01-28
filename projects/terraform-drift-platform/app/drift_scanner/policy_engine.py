from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .models import (
  Category,
  DriftAction,
  DriftChange,
  PolicyDecision,
  Recommendation,
  Severity,
)


@dataclass
class PolicyRule:
  name: str
  match: Dict[str, Any]
  conditions: Dict[str, Any]
  severity: Severity
  category: Category
  recommendation: Recommendation


@dataclass
class PolicySet:
  default: PolicyDecision
  rules: List[PolicyRule]


def load_policies(path: Path) -> PolicySet:
  data = yaml.safe_load(path.read_text())
  default_cfg = data.get("default", {}) or {}
  rules_cfg = data.get("rules", []) or []

  default_decision = PolicyDecision(
    severity=Severity(default_cfg.get("severity", "LOW")),
    category=Category(default_cfg.get("category", "OTHER")),
    recommendation=Recommendation(default_cfg.get("recommendation", "REVIEW")),
    rule_name=None,
  )

  rules: List[PolicyRule] = []
  for rc in rules_cfg:
    rules.append(
      PolicyRule(
        name=rc["name"],
        match=rc.get("match", {}) or {},
        conditions=rc.get("conditions", {}) or {},
        severity=Severity(rc["severity"]),
        category=Category(rc["category"]),
        recommendation=Recommendation(rc["recommendation"]),
      )
    )

  return PolicySet(default=default_decision, rules=rules)


def _match_rule(change: DriftChange, rule: PolicyRule) -> bool:
  m = rule.match

  rtype = m.get("resource_type")
  if rtype and rtype != "*" and rtype != change.resource_type:
    return False

  envs = m.get("environments")
  if envs and change.environment not in envs:
    return False

  actions = m.get("actions")
  if actions:
    change_actions = {a.value for a in change.actions}
    if change_actions.isdisjoint(set(actions)):
      return False

  # Conditions are evaluated in a very simple, conservative way here.
  conds = rule.conditions
  if not conds:
    return True

  # Example: tag_only, network_widening, public_access_changed etc.
  # Implementations can expand this significantly; here we implement a few
  # simple heuristics.
  if conds.get("tag_only"):
    before = change.before or {}
    after = change.after or {}
    # Heuristic: if only "tags" changed (keys and values), treat as tag_only.
    def _strip_tags(d: Dict[str, Any]) -> Dict[str, Any]:
      return {k: v for k, v in d.items() if k != "tags"}

    if _strip_tags(before) != _strip_tags(after):
      return False

  # network_widening and public_access_changed require more domain knowledge.
  # Here we only assert they must be flagged earlier in a preprocessing stage.
  # For now we assume the parser would set special markers, which this simple
  # reference implementation does not, so we treat them as unsupported unless
  # explicitly set via before/after hints.

  return True


def evaluate_policies(
  policies: PolicySet, change: DriftChange
) -> PolicyDecision:
  for rule in policies.rules:
    if _match_rule(change, rule):
      return PolicyDecision(
        severity=rule.severity,
        category=rule.category,
        recommendation=rule.recommendation,
        rule_name=rule.name,
      )

  # Fallback to default
  return PolicyDecision(
    severity=policies.default.severity,
    category=policies.default.category,
    recommendation=policies.default.recommendation,
    rule_name=None,
  )

