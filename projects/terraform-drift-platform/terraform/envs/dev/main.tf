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
  description = "AWS region for dev environment."
  default     = "us-east-1"
}

module "drift_platform" {
  source = "../../modules/drift-platform"

  environment         = "dev"
  region              = var.region
  dynamodb_table_name = "drift-audit-dev"
  reports_bucket_name = "drift-reports-dev-example"
  sns_topic_name      = "drift-notifications-dev"
}

