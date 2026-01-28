terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

variable "environment" {
  type        = string
  description = "Environment name (e.g. dev, prod)."
}

variable "region" {
  type        = string
  description = "AWS region."
}

variable "dynamodb_table_name" {
  type        = string
  description = "Name of the DynamoDB table for drift audit records."
}

variable "reports_bucket_name" {
  type        = string
  description = "Name of the S3 bucket for drift reports."
}

variable "sns_topic_name" {
  type        = string
  description = "Name of the SNS topic for drift notifications."
}

resource "aws_dynamodb_table" "drift_audit" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Component   = "drift-platform"
  }
}

resource "aws_s3_bucket" "drift_reports" {
  bucket = var.reports_bucket_name

  tags = {
    Environment = var.environment
    Component   = "drift-platform"
  }
}

resource "aws_sns_topic" "drift_notifications" {
  name = var.sns_topic_name

  tags = {
    Environment = var.environment
    Component   = "drift-platform"
  }
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.drift_audit.name
}

output "reports_bucket_name" {
  value = aws_s3_bucket.drift_reports.bucket
}

output "sns_topic_arn" {
  value = aws_sns_topic.drift_notifications.arn
}

