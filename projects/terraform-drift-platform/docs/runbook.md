# Terraform Drift Detection Platform – Runbook

This runbook describes how to **operate**, **monitor**, and **troubleshoot**
the Terraform Drift Detection & Auto-Remediation Platform.

---

## 1. Responsibilities & Contacts

Intended operators:

- Site Reliability Engineering / Platform teams
- Security Engineering (for policy tuning on security-sensitive resources)

Key shared responsibilities:

- Keep Terraform modules and environments up to date.
- Maintain and review drift policies.
- Monitor drift events and remediation outcomes.

---

## 2. Environments

- **dev**
  - Used for initial deployments, testing policies, and validating drift
    detection behavior.
  - Lower-risk resources and permissive IAM where appropriate.

- **prod**
  - Used for production workloads and accounts.
  - Stricter IAM, more conservative policies, stronger notifications.

Both environments follow the same structure under
`terraform/envs/{dev,prod}`.

---

## 3. Routine Operations

### 3.1 Checking Recent Drift Events

Drift events are stored in:

- **DynamoDB** – summary and status
- **S3** – detailed JSON reports

Typical queries:

- “Show high/critical drift in prod over the last 24 hours.”
- “Confirm whether remediation has been applied for drift ID X.”

Use:

- DynamoDB console queries
- Internal tooling / CLI (e.g., future enhancement) querying the audit table

### 3.2 Reviewing Notifications

Subscriptions to the SNS topic should include:

- Shared distribution lists (SRE, security, platform)
- Chat channels for real-time visibility

Operators should:

- Quickly scan notifications for **CRITICAL/HIGH** severity drift.
- Confirm that remediation or manual action is planned.

---

## 4. Onboarding a New Environment or Account

To onboard a new AWS account or environment:

1. **Create/Update Terraform configuration**
   - Add the account/environment to:
     - `terraform/envs/dev` or `terraform/envs/prod` as appropriate.
   - Configure the state backend for the new account.

2. **Deploy cross-account roles**
   - Use `terraform/modules/cross-account-role` to create a role in the target
     account.
   - Ensure the central scanner account is allowed to assume the role.

3. **Bootstrap Terraform state**
   - Ensure Terraform is managing the target resources.
   - Run an initial `terraform apply` to align the account to the desired state.

4. **Add policies if needed**
   - Update `policies/drift_policies.yml` to include environment- or
     account-specific rules.

5. **Test in dev**
   - Introduce safe drift in the new environment.
   - Validate detection, classification, and notifications.

---

## 5. Responding to Drift

### 5.1 General Response Workflow

1. **Triage**
   - Review the notification and its severity.
   - Look up the detailed report in S3 if more context is needed.

2. **Decide on action**
   - If severity is `LOW/MEDIUM` and recommendation is `AUTO_REMEDIATE`, it may
     be safe to approve automation.
   - For `HIGH/CRITICAL`, follow your incident/change management process.

3. **Apply remediation**
   - Use `terraform apply` directly (following change management policies), or
   - Use the GitHub Issue + Actions workflow to apply remediation.

4. **Verify**
   - Confirm that the drift no longer appears in subsequent scans.
   - Ensure no unintended side effects occurred.

### 5.2 Using GitHub Issues for Approval

When configured, the scanner can create or update GitHub Issues for certain
drift events.

Operator steps:

1. Open the referenced GitHub Issue.
2. Review the:
   - Drift summary
   - Severity and category
   - Proposed remediation action
3. If acceptable:
   - Add an approval label (e.g., `approved-for-remediation`), or
   - Add a specific approval comment (as defined in the workflow).
4. The `apply-approved-remediation.yml` workflow will:
   - Run `terraform apply`
   - Update the Issue with results
   - Optionally update the audit record (if API integration is enabled)

---

## 6. Common Tasks

### 6.1 Updating Policies

1. Edit `policies/drift_policies.yml` in a feature branch.
2. Open a Pull Request.
3. Have relevant teams (e.g., Security, SRE) review the changes.
4. Merge after approval and let automation roll out updates.

### 6.2 Adding New Resource Types

If you add new Terraform resources:

1. Extend `plan_parser.py` (if needed) to capture relevant attributes.
2. Add or adjust policies for the new resource types.
3. Test in a non-production environment to confirm expected behavior.

---

## 7. Troubleshooting

### 7.1 Drift Not Detected

**Symptoms**

- Terraform configuration changed, but detector reports “no drift”.

**Checks**

1. Verify Terraform is run with `-refresh-only`:
   - The platform compares *live resources to state*, not config changes that
     have not been applied.
2. Confirm the environment/account is in scope:
   - Check configuration in the drift scanner (env list, accounts).
3. Ensure the cross-account role has adequate read permissions.

### 7.2 False Positives or Overly Noisy Drift

**Symptoms**

- Drift is reported frequently for benign changes (e.g., timestamp fields,
  non-critical tags).

**Actions**

1. Review the detailed S3 report for the drift.
2. Identify whether certain attributes can be:
   - Ignored in parsing, or
   - Mapped to `LOW` severity via policy.
3. Update `plan_parser.py` or `drift_policies.yml` as needed.

### 7.3 Lambda or CLI Fails to Run Terraform

**Symptoms**

- Errors such as “terraform: command not found” or failed provider auth.

**Actions**

1. Confirm Terraform is installed in the runtime environment.
2. Ensure the correct working directory and `terraform init` have been run.
3. Verify AWS credentials:
   - Lambda execution role permissions.
   - STS AssumeRole capabilities for target accounts.

---

## 8. DR / Backup & Restore

### 8.1 Audit Data

- **DynamoDB**:
  - Enable PITR (Point-in-Time Recovery) if available in your environment.
  - For critical environments, consider periodic exports to S3.

- **S3 Reports**:
  - Enable versioning and, if needed, object lock for compliance.

### 8.2 Terraform State

- Terraform state should already be protected using:
  - Versioned S3 buckets (or other backends).
  - Restricted access via IAM.

Recovery steps generally involve:

1. Restoring DynamoDB and/or S3 from backup or previous versions.
2. Re-deploying the scanner and infrastructure via Terraform.

---

## 9. Change Management

- Treat all changes to:
  - Terraform code,
  - Drift policies,
  - IAM roles and permissions,
  as **code changes** reviewed via Pull Requests.

- For production:
  - Require at least one approving review from SRE/Security.
  - Use GitHub Protected Branches and CI checks.

---

## 10. Escalation

In case of:

- Repeated **CRITICAL** drift
- Suspected compromise of Terraform state or AWS credentials

Follow your organization’s **incident response** plan. As a baseline:

1. Pause auto-remediation workflows.
2. Rotate credentials and examine access logs.
3. Involve security incident responders.

