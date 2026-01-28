# Personal Engineering Portfolio & Terraform Drift Platform

This repository is my **primary personal engineering portfolio** and home for a
senior-level infrastructure project:

- **Terraform Drift Detection & Auto-Remediation Platform**
- A static **Astro-based portfolio site** that presents this and future projects

Everything lives in this single repo so it is easy to clone, explore, and
extend over time.

---

## Repository Structure

- **`projects/terraform-drift-platform/`** – Production-style infrastructure project
  for detecting and remediating Terraform drift across AWS accounts.
- **`site/`** – Astro-based personal portfolio website, deployable to GitHub Pages.

High-level layout:

- `projects/terraform-drift-platform`
  - `docs/` – architecture, runbook, threat model
  - `policies/` – YAML policy definitions for drift classification
  - `terraform/` – reusable modules and environment definitions
  - `app/` – Python 3.11 implementation (Lambda-style handler + CLI tools)
  - `tests/` – unit tests for key logic
  - `.github/workflows/` – example CI workflows for drift checks and remediation
- `site/`
  - Astro configuration, pages, layouts, components, and GitHub Pages workflow

---

## Running the Astro Portfolio Site Locally

Requirements:
- Node.js 18+ (LTS recommended)
- npm or pnpm

From the repo root:

```bash
cd site
npm install
npm run dev
```

Then open the printed `http://localhost:xxxx` URL in your browser.

The homepage shows my profile and a **Personal Projects** section with the
Terraform Drift Detection & Auto-Remediation Platform. The **Projects** page
provides more detail and links into the project documentation in this repo.

---

## Deploying the Portfolio Site (GitHub Pages)

The Astro site is designed to be deployed to GitHub Pages using GitHub Actions.

1. Ensure this repository is pushed to GitHub and that `main` is the default branch.
2. In GitHub:
   - Go to **Settings → Pages**
   - Set **Source** to **GitHub Actions**
3. The workflow file at:
   - `site/.github/workflows/deploy-pages.yml`
   will:
   - Install dependencies
   - Build the Astro site (`npm run build`)
   - Copy the `projects/` docs into the built site so documentation is reachable
   - Publish the static assets to GitHub Pages

On each push to `main`, the site will be rebuilt and redeployed.

---

## Running Drift Detection Locally

The core drift detection logic lives in:

- `projects/terraform-drift-platform/app/drift_scanner/`

Key modules:

- `handler.py` – Lambda-style entrypoint for scheduled drift scans
- `terraform_runner.py` – runs Terraform plan/show commands
- `plan_parser.py` – parses Terraform JSON plans into typed models
- `policy_engine.py` – classifies drift using YAML policies
- `audit.py` – writes audit records to DynamoDB and detailed reports to S3
- `notify.py` – sends notifications via SNS
- `config.py` – strongly-typed configuration from environment variables

To run a local drift check (simulating what Lambda would do), from repo root:

```bash
cd projects/terraform-drift-platform/app/drift_scanner
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Example (using an env directory with Terraform already initialized)
python handler.py --env-path ../../terraform/envs/dev
```

You will need:
- Terraform installed and initialized in the target `envs/<env>` directory
- AWS credentials configured (e.g., via `aws configure` or environment variables)

See `projects/terraform-drift-platform/README.md` for detailed configuration
and examples.

---

## Deploying Terraform (Dev Environment)

The Terraform project is laid out with:

- Reusable modules under `projects/terraform-drift-platform/terraform/modules/`
- Environment definitions under `projects/terraform-drift-platform/terraform/envs/`

To deploy the **dev** environment:

```bash
cd projects/terraform-drift-platform/terraform/envs/dev
terraform init
terraform plan
terraform apply
```

The dev environment is intentionally minimal and focuses on:

- DynamoDB table for audit history
- S3 bucket for full drift reports
- SNS topic for notifications
- IAM roles and policies for:
  - The drift scanner Lambda
  - Cross-account role assumption into target accounts

The **prod** environment under `envs/prod` follows the same pattern but should be
configured with production-grade settings (e.g., tighter IAM, larger capacity,
stricter alarms).

For a full explanation of the Terraform resources and flows, see:

- `projects/terraform-drift-platform/docs/architecture.md`

---

## Future Projects

This repository is meant to grow over time. Future additions may include:

- Additional infrastructure platforms (e.g., cost anomaly detection, multi-cloud
  posture management)
- Backend services and APIs (Python / Go / Java)
- Frontend dashboards (React, Astro islands, or similar)
- Data engineering and analytics projects

New projects will live under `projects/` and will be surfaced in the Astro
portfolio site via new project cards and detail pages.

