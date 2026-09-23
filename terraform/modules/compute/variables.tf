variable "environment" {
  description = "Deployment environment name (e.g. staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where compute resources reside"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "api_image_tag" {
  description = "Docker image tag for TrustMoss API"
  type        = string
  default     = "latest"
}

variable "web_image_tag" {
  description = "Docker image tag for TrustMoss Web"
  type        = string
  default     = "latest"
}

variable "api_cpu" {
  description = "Fargate CPU units for API (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "api_memory" {
  description = "Fargate Memory (MB) for API"
  type        = number
  default     = 2048
}

variable "api_desired_count" {
  description = "Desired number of running API task instances"
  type        = number
  default     = 2
}

variable "web_cpu" {
  description = "Fargate CPU units for Web (512 = 0.5 vCPU)"
  type        = number
  default     = 512
}

variable "web_memory" {
  description = "Fargate Memory (MB) for Web"
  type        = number
  default     = 1024
}

variable "web_desired_count" {
  description = "Desired number of running Web task instances"
  type        = number
  default     = 2
}

variable "database_url" {
  description = "PostgreSQL connection string"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Redis connection string"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
