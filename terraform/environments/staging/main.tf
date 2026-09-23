terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for remote state (e.g. S3 + DynamoDB locking)
  # backend "s3" {
  #   bucket         = "trustmoss-terraform-state-staging"
  #   key            = "staging/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "trustmoss-terraform-locks-staging"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "TrustMoss"
      Environment = "staging"
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  environment = "staging"
  tags = {
    Project     = "TrustMoss"
    Environment = "staging"
  }
}

module "networking" {
  source = "../../modules/networking"

  environment          = local.environment
  vpc_cidr             = "10.10.0.0/16"
  availability_zones   = ["${var.aws_region}a", "${var.aws_region}b"]
  public_subnet_cidrs  = ["10.10.1.0/24", "10.10.2.0/24"]
  private_subnet_cidrs = ["10.10.10.0/24", "10.10.11.0/24"]
  enable_nat_gateway   = true
  tags                 = local.tags
}

module "database" {
  source = "../../modules/database"

  environment                = local.environment
  vpc_id                     = module.networking.vpc_id
  subnet_ids                 = module.networking.private_subnet_ids
  allowed_security_group_ids = [module.compute.ecs_security_group_id]
  db_instance_class          = "db.t4g.micro"
  db_allocated_storage       = 20
  db_multi_az                = false
  redis_node_type            = "cache.t4g.micro"
  redis_num_cache_nodes      = 1
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
  api_cpu            = 512
  api_memory         = 1024
  api_desired_count  = 1
  web_cpu            = 256
  web_memory         = 512
  web_desired_count  = 1
  database_url       = "postgresql://trustmoss_admin:secret@${module.database.db_endpoint}/${module.database.db_name}"
  redis_url          = "redis://${module.database.redis_primary_endpoint}:${module.database.redis_port}/0"
  tags               = local.tags
}
