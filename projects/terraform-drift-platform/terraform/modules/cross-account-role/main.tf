terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

variable "role_name" {
  type        = string
  description = "Name of the cross-account role."
}

variable "trusted_account_id" {
  type        = string
  description = "AWS account ID of the central scan account."
}

variable "policy_json" {
  type        = string
  description = "JSON IAM policy granting least-privilege access to managed resources."
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "cross_account" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.trusted_account_id}:root"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "inline" {
  name   = "${var.role_name}-policy"
  role   = aws_iam_role.cross_account.id
  policy = var.policy_json
}

output "role_arn" {
  value = aws_iam_role.cross_account.arn
}

