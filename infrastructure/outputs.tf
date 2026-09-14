output "aws_region" {
  value = var.aws_region
}

output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "eks_cluster_arn" {
  value = aws_eks_cluster.main.arn
}

output "ingestion_api_ecr_url" {
  value = aws_ecr_repository.ingestion_api.repository_url
}

output "incident_api_ecr_url" {
  value = aws_ecr_repository.incident_api.repository_url
}

output "incidents_table_name" {
  value = aws_dynamodb_table.incidents.name
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}