terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for remote state
  # backend "s3" {
  #   bucket         = "trustmoss-terraform-state-production"
  #   key            = "production/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "trustmoss-terraform-locks-production"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TrustMoss"
      Environment = "production"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  environment = "production"
  tags = {
    Project     = "TrustMoss"
    Environment = "production"
  }
}

module "networking" {
  source = "../../modules/networking"

  environment          = local.environment
  vpc_cidr             = "10.20.0.0/16"
  availability_zones   = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnet_cidrs  = ["10.20.1.0/24", "10.20.2.0/24"]
  private_subnet_cidrs = ["10.20.10.0/24", "10.20.11.0/24"]
  enable_nat_gateway   = true
  tags                 = local.tags
}

module "database" {
  source = "../../modules/database"

  environment                = local.environment
  vpc_id                     = module.networking.vpc_id
  subnet_ids                 = module.networking.private_subnet_ids
  allowed_security_group_ids = [module.compute.ecs_security_group_id]
  db_instance_class          = "db.t4g.small"
  db_allocated_storage       = 50
  db_multi_az                = true
  redis_node_type            = "cache.t4g.small"
  redis_num_cache_nodes      = 2
  tags                       = local.tags
}

module "compute" {
  source = "../../modules/compute"

  environment        = local.environment
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  api_image_tag      = var.api_image_tag
  web_image_tag      = var.web_image_tag
  api_cpu            = 1024
  api_memory         = 2048
  api_desired_count  = var.api_desired_count
  web_cpu            = 512
  web_memory         = 1024
  web_desired_count  = var.web_desired_count
  database_url       = "postgresql://trustmoss_admin:secret@${module.database.db_endpoint}/${module.database.db_name}"
  redis_url          = "redis://${module.database.redis_primary_endpoint}:${module.database.redis_port}/0"
  tags               = local.tags
}
