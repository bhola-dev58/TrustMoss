output "alb_dns_name" {
  description = "Production public ALB address"
  value       = module.compute.alb_dns_name
}

output "api_ecr_repository_url" {
  description = "Production ECR repository for API"
  value       = module.compute.api_ecr_repository_url
}

output "web_ecr_repository_url" {
  description = "Production ECR repository for Web"
  value       = module.compute.web_ecr_repository_url
}

output "ecs_cluster_name" {
  description = "Production ECS Cluster name"
  value       = module.compute.ecs_cluster_name
}

output "database_endpoint" {
  description = "Production RDS connection endpoint"
  value       = module.database.db_endpoint
}
