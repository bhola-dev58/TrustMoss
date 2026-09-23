variable "environment" {
  description = "Deployment environment name (e.g. staging, production)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where database resources reside"
  type        = string
}

variable "subnet_ids" {
  description = "Private subnet IDs for database deployment"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "List of security groups permitted to access database and cache"
  type        = list(string)
  default     = []
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.small"
}

variable "db_allocated_storage" {
  description = "Allocated storage in gigabytes"
  type        = number
  default     = 20
}

variable "db_multi_az" {
  description = "Specifies if the RDS instance is multi-AZ"
  type        = bool
  default     = false
}

variable "db_name" {
  description = "Name of the default database to create"
  type        = string
  default     = "trustmoss"
}

variable "db_username" {
  description = "Master username for database"
  type        = string
  default     = "trustmoss_admin"
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes in Redis cluster"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
