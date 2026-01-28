## Terraform Drift Detection & Auto-Remediation Platform

### Overview

This project detects when **live AWS infrastructure** diverges from the
**Terraform-defined desired state**, classifies the severity of each drift
event, records a detailed audit trail, and optionally supports
**approval-based remediation**.

The system is designed as an internal enterprise platform with:

- Clear separation between **drift detection**, **policy evaluation**,
  **audit logging**, and **notification/remediation**
- Strong emphasis on **least privilege**, **observability**, and **safety**
- Integration points for **GitHub Actions** and an optional
  **approval workflow** using GitHub Issues

---

### High-Level Flow

1. A scheduled process (e.g., EventBridge or GitHub Actions) triggers the
   **drift scanner**.
2. The scanner:
   - Iterates over configured AWS accounts/environments
   - Runs `terraform plan -refresh-only -detailed-exitcode`
   - If drift is detected, runs `terraform show -json tfplan`
3. The **plan parser** converts the Terraform JSON into typed Python models
   describing the drift (resources, attributes, actions).
4. The **policy engine** evaluates drift against policies from
   `policies/drift_policies.yml` and assigns a **severity** and recommended
   **action**.
5. The **audit layer**:
   - Writes a compact audit record to DynamoDB
   - Stores a full report (JSON) in S3
6. The **notification layer** sends a JSON summary to SNS subscribers, which
   may include:
   - ChatOps (Slack, Teams, email)
   - Incident management tools (PagerDuty, Opsgenie)
7. For high/critical drift, the platform can create or update **GitHub Issues**
   representing remediation items. Application of remediation is gated by
   approval semantics.

---

### Architecture

See `docs/architecture.md` for full details and diagrams.

At a glance:

- **Drift Scanner (Lambda / CLI)**:
  - Executes Terraform commands in a controlled environment
  - Produces normalized drift events
- **Policy Engine**:
  - Loads YAML policies defining:
    - Which resources are in scope
    - Severity mapping rules
    - Auto-remediation eligibility
- **Audit & Storage**:
  - DynamoDB: fast lookup of drift history and status
  - S3: immutable JSON reports for compliance and forensics
- **Notification & Remediation**:
  - SNS: delivers drift events to downstream consumers
  - Optional GitHub Issues + GitHub Actions workflows for
    approval-based remediation

```mermaid
flowchart LR
  Scheduler[Scheduler\n(EventBridge / GitHub Actions)]
    --> Scanner[Drift Scanner\n(Lambda or CLI)]
  Scanner --> Terraform[Terraform CLI\nplan + show -json]
  Scanner --> Parser[Plan Parser]
  Parser --> Policy[Policy Engine\n(drift_policies.yml)]
  Policy --> Audit[Audit Writer\n(DynamoDB + S3)]
  Policy --> Notify[Notifier\n(SNS)]
  Notify --> GH[GitHub Issues\n(optional)]
  GH --> GA[GitHub Actions\nRemediation Workflow]
```

---

### How Drift Is Detected

The core of drift detection relies on **Terraform’s own planning engine**.

For each environment:

1. Run:
   ```bash
   terraform plan -refresh-only -detailed-exitcode -out=tfplan
   ```
2. Interpret exit code:
   - `0` – No drift, desired and actual state match
   - `1` – Error
   - `2` – Drift detected (changes would be applied)
3. On exit code `2`, run:
   ```bash
   terraform show -json tfplan > tfplan.json
   ```
4. The scanner reads `tfplan.json` and passes it to the **plan parser**, which
   builds a normalized list of `DriftChange` items describing:
   - Resource address and type
   - Change action (`create`, `update`, `delete`, `replace`)
   - Key attributes that changed

Because we rely on Terraform’s own `-refresh-only` behavior, we only detect
drift between live remote resources and state, not un-applied configuration
changes in code.

---

### How Severity Is Determined

Severity is derived by the **policy engine**, which reads
`policies/drift_policies.yml`. Policies may consider:

- Resource type (`aws_iam_role`, `aws_security_group`, `aws_s3_bucket`, etc.)
- Environment (`dev`, `prod`)
- Change action (`update`, `delete`, etc.)
- Specific attributes (e.g., public access, encryption flags, CIDR ranges)

Example policy concepts:

- Any drift on **production IAM roles** or **security groups** is at least
  **High**.
- Drift that **widens network access** (e.g., `0.0.0.0/0` added) is **Critical**.
- Drift on **non-prod compute scaling** might be **Low** or **Medium**.

The engine emits:

- A **severity** (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- A **category** (e.g., `SECURITY`, `AVAILABILITY`, `COST`)
- A **recommended action** (`IGNORE`, `REVIEW`, `AUTO_REMEDIATE`)

---

### Approval-Based Remediation

The platform supports **optional auto-remediation** with approval semantics:

1. For drift where policy recommends `AUTO_REMEDIATE`, the scanner can:
   - Create (or update) a **GitHub Issue** in a designated repo
   - Attach the drift report and an explanation of the proposed fix
2. A **GitHub Actions workflow** (`.github/workflows/apply-approved-remediation.yml`)
   can be configured to:
   - Trigger on labeled Issues or specific comments
   - Run `terraform apply` with the saved plan or a fresh plan
   - Log results back to the Issue and to the audit trail

This keeps engineers **in the loop** while enabling fast, repeatable fixes:

- Policies decide which drift *can* be auto-remediated.
- Human approval (or explicit labels) decide when it *should* be applied.

---

### How to Test Drift Safely

To avoid unintended production changes, use **sandbox or dev accounts** and
safe test scenarios.

1. **Clone the repository** and set up a non-production AWS account.
2. Deploy the **dev** Terraform environment:
   ```bash
   cd projects/terraform-drift-platform/terraform/envs/dev
   terraform init
   terraform apply
   ```
3. Introduce intentional drift:
   - Modify a tag on an EC2 instance from the AWS console.
   - Temporarily change a security group description.
   - Adjust a non-critical parameter (e.g., retention days) on a log group.
4. Run the drift scanner locally as described in this README.
5. Validate:
   - Drift is detected and visible in logs
   - A record is written to the audit table and S3 (if configured)
   - Notifications are sent via SNS (if configured)

Never test new or experimental policies directly against production accounts.

---

### Documentation

Full documentation is under `docs/`:

- `architecture.md` – detailed architecture, data flows, and diagrams
- `runbook.md` – operational procedures and troubleshooting
- `threat_model.md` – trust boundaries, threats, and mitigations

---

### Local Development

1. **Python environment**

   ```bash
   cd projects/terraform-drift-platform/app/drift_scanner
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run unit tests**

   ```bash
   cd ../../..
   python -m venv .venv
   source .venv/bin/activate
   pip install -r app/drift_scanner/requirements.txt
   pip install -r app/cli/requirements.txt
   pip install pytest

   pytest tests
   ```

3. **CLI usage examples**

   See `app/cli/drift_check.py` and `app/cli/remediation_apply.py` for
   example commands to run drift checks and apply remediation from a local
   workstation or CI pipeline.

---

### GitHub Actions Integration

Under `.github/workflows/` in this project:

- `drift-check.yml` – example workflow to run drift checks on a schedule or on
  push, publishing results and artifacts.
- `apply-approved-remediation.yml` – example workflow to apply remediation when
  a GitHub Issue is approved or labeled appropriately.

These workflows are templates and should be adapted to your organization’s
branching, approval, and secrets-management practices.

