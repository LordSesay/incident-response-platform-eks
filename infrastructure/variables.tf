variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name for project resources"
  type        = string
  default     = "incident-response"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "eks_cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "incident-response-eks"
}

variable "kubernetes_version" {
  # Check support dates before changing: aws eks describe-cluster-versions
  # EKS upgrades one minor version at a time, so an existing cluster must step through each version.
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.35"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "desired_size" {
  description = "Desired node count"
  type        = number
  default     = 2
}

variable "min_size" {
  description = "Minimum node count"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum node count"
  type        = number
  default     = 3
}

variable "incidents_table_name" {
  description = "DynamoDB incidents table name"
  type        = string
  default     = "incident-response-incidents"
}