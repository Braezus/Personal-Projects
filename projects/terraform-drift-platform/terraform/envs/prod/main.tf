terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type        = string
  description = "AWS region for prod environment."
  default     = "us-east-1"
}

module "drift_platform" {
  source = "../../modules/drift-platform"

  environment         = "prod"
  region              = var.region
  dynamodb_table_name = "drift-audit-prod"
  reports_bucket_name = "drift-reports-prod-example"
  sns_topic_name      = "drift-notifications-prod"
}

