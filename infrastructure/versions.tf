terraform {
  # 1.10+ is required for S3 native state locking (use_lockfile).
  required_version = ">= 1.10.0"

  # Partial configuration: supply account-specific settings at init time with
  # terraform init -backend-config=backend.hcl (see backend.hcl.example).
  backend "s3" {}

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}