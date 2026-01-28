# Terraform Drift Detection & Auto-Remediation Platform – Architecture

## 1. Goals

- Detect drift between **Terraform configuration/state** and **live AWS
  infrastructure**.
- Classify drift by **severity** and **category** using policy files.
- Maintain a durable **audit trail** for compliance and forensics.
- Provide hooks for **notification** and **approval-based remediation**.
- Support **multi-account** environments with **least-privilege** access.

---

## 2. High-Level Architecture

```mermaid
flowchart LR
  subgraph AWS
    Scheduler[EventBridge\nCron Schedule]
    LambdaScanner[Drift Scanner Lambda]
    TerraformCLI[Terraform CLI\n(plan + show)]
    Dynamo[DynamoDB\nDrift Audit Table]
    S3Reports[S3\nDrift Reports Bucket]
    SNS[Amazon SNS\nNotifications]
    TargetAcct[Target AWS Accounts\n(Cross-Account Roles)]
  end

  subgraph GitHub
    Repo[GitHub Repo\n(Infra + Policies)]
    Issues[GitHub Issues\nRemediation Items]
    GHActions[GitHub Actions\nWorkflows]
  end

  Scheduler --> LambdaScanner
  LambdaScanner --> TerraformCLI
  TerraformCLI --> LambdaScanner
  LambdaScanner --> Dynamo
  LambdaScanner --> S3Reports
  LambdaScanner --> SNS
  LambdaScanner --> Issues
  SNS -->|optional| ExternalTools[ChatOps / Incident Mgmt]
  GHActions --> TerraformCLI
  Issues --> GHActions
  LambdaScanner --> TargetAcct
```

### Components

- **Drift Scanner (Lambda / CLI)**
  - Executes Terraform commands and parses JSON plans.
  - Applies policies to compute severity and recommended actions.
  - Writes audit records and sends notifications.

- **Terraform CLI**
  - Runs with `-refresh-only -detailed-exitcode` to detect drift without
    changing infrastructure.
  - Produces machine-readable JSON plans with `terraform show -json`.

- **Policy Engine**
  - Loads rules from `policies/drift_policies.yml`.
  - Maps resource-level drift to severities and remediation guidance.

- **Audit Trail**
  - DynamoDB for quick queries across many drift events.
  - S3 for immutable, detailed JSON reports.

- **Notifications & Remediation**
  - SNS for asynchronous notifications and fan-out.
  - GitHub Issues and Actions provide a human approval layer for remediation.

---

## 3. Drift Detection Flow

### 3.1 Trigger

Drift detection can be triggered by:

- **AWS EventBridge** rule on a fixed schedule (e.g., every 30 minutes).
- **GitHub Actions** workflow (e.g., nightly or on-demand).
- Manual invocation via CLI for ad hoc checks.

### 3.2 Terraform Plan

For each environment/account combination, the scanner:

1. Prepares a working directory with Terraform configuration and state backend.
2. Runs:
   ```bash
   terraform plan -refresh-only -detailed-exitcode -out=tfplan
   ```
3. Interprets exit code:
   - `0` – No drift.
   - `1` – Error (configuration or provider failure).
   - `2` – Drift detected.
4. If drift is detected, runs:
   ```bash
   terraform show -json tfplan > tfplan.json
   ```

### 3.3 Plan Parsing & Normalization

`plan_parser.py` reads `tfplan.json` and converts it into typed models:

- `DriftChange`
  - resource address
  - resource type
  - action(s) (`create`, `update`, `delete`, `replace`)
  - key before/after attributes (summarized)

The parser intentionally focuses on **signal-bearing attributes**, not every
field in the plan, to make policy evaluation and notifications clearer.

---

## 4. Policy Engine

`policy_engine.py` is responsible for:

- Loading `policies/drift_policies.yml`.
- Matching each `DriftChange` against policy rules.
- Assigning:
  - **severity** (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
  - **category** (`SECURITY`, `AVAILABILITY`, `COST`, `OTHER`)
  - **recommendation** (`IGNORE`, `REVIEW`, `AUTO_REMEDIATE`)

Example rule concepts:

- Any drift on production `aws_security_group` that broadens CIDR is
  **CRITICAL/SECURITY** and not auto-remediated.
- Non-prod `aws_s3_bucket` tagging drift may be **LOW/OTHER** and auto-remediable.

The policy engine is **data-driven**; adding new rules does not require code
changes, only updates to the YAML.

---

## 5. Audit & Storage

### 5.1 DynamoDB

Used for a compact, queryable record of drift events:

- Partition key: `environment#account_id`
- Sort key: `timestamp#drift_id`
- Attributes:
  - Severity, category, resource counts
  - References to S3 report keys
  - Status (e.g., `DETECTED`, `REMEDIATION_APPLIED`, `IGNORED`)

This allows operations and security teams to quickly answer:

- “What drift did we see in prod this week?”
- “How many high-severity events were auto-remediated vs manually reviewed?”

### 5.2 S3

Stores **full JSON reports**:

- Key format:
  - `env=<env>/account=<id>/drift/<timestamp>_<drift_id>.json`
- Payload:
  - Raw or normalized plan details
  - Policies applied and decisions taken
  - Any remediation actions or links to GitHub issues

S3 data supports longer-term compliance, forensics, and offline analysis.

---

## 6. Notifications & GitHub Integration

### 6.1 SNS

SNS topics receive structured JSON messages for each drift event:

- Environment and account
- Severity and category
- High-level counts (resources changed, actions, etc.)
- Links to S3 reports and, if enabled, GitHub Issues

Downstream consumers:

- Email/SMS
- ChatOps (Slack, Teams)
- Incident tools

### 6.2 GitHub Issues & Actions

For high/critical severity or `AUTO_REMEDIATE` decisions, the scanner may:

- Create or update a **GitHub Issue** in a repo.
- Attach drift summaries and links to reports.

The corresponding GitHub Action:

- Runs when an Issue is labeled (e.g., `approved-for-remediation`) or a
  specific comment is added.
- Executes `terraform apply` using the same configuration and plan.
- Updates the Issue with outcome and updates the audit status via the API.

This creates a clear, auditable approval trail for sensitive changes.

---

## 7. Multi-Account & Cross-Account Roles

The platform assumes a **central scan account** that:

- Hosts the scanner Lambda and related infrastructure.
- Assumes **cross-account IAM roles** in target accounts to read and compare
  resources against Terraform state.

`terraform/modules/cross-account-role` defines:

- A role in each target account with:
  - Trust relationship granting the scan account permission to assume it.
  - Least-privilege read access to resources under management.

The scanner uses STS `AssumeRole` to:

- Temporarily obtain credentials for each target account.
- Run `terraform plan` with the correct AWS context.

---

## 8. Security Posture

Key principles:

- **Least privilege** IAM for:
  - Scanner Lambda execution role
  - Cross-account roles
  - Access to DynamoDB, S3, and SNS
- **Strong separation of duties**:
  - Detection and classification are automated.
  - Remediation can be gated by human approval.
- **Immutable audit trail**:
  - S3 can be configured with object lock / versioning.
  - DynamoDB history is append-only at the platform level.
- **Configuration as code**:
  - Terraform definitions and policies are version-controlled.

More detailed analysis is provided in `threat_model.md`.

---

## 9. Extensibility

The architecture is designed to be extended:

- Add new policy types without changing code.
- Support additional cloud providers by:
  - Adding alternative plan runners and parsers.
  - Reusing the same policy engine and audit/notification layers.
- Integrate with additional approval systems (e.g., ServiceNow, internal
  change management) by adding new notification adapters.

