resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_subnet_group" "rds" {
  name       = "trustmoss-${var.environment}-db-subnets"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name        = "trustmoss-${var.environment}-db-subnets"
    Environment = var.environment
  })
}

resource "aws_security_group" "rds" {
  name        = "trustmoss-${var.environment}-rds-sg"
  description = "Controls access to PostgreSQL RDS"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from permitted compute security groups"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "trustmoss-${var.environment}-rds-sg"
    Environment = var.environment
  })
}

resource "aws_db_instance" "postgres" {
  identifier             = "trustmoss-${var.environment}-postgres"
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = var.db_instance_class
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_allocated_storage * 5
  storage_type           = "gp3"
  db_name                = var.db_name
  username               = var.db_username
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = var.db_multi_az
  skip_final_snapshot    = var.environment == "staging" ? true : false
  final_snapshot_identifier = var.environment == "staging" ? null : "trustmoss-${var.environment}-final-snapshot"
  deletion_protection    = var.environment == "production" ? true : false

  backup_retention_period = var.environment == "production" ? 14 : 3
  backup_window           = "03:00-04:00"
  maintenance_window      = "Sun:04:30-Sun:05:30"

  tags = merge(var.tags, {
    Name        = "trustmoss-${var.environment}-postgres"
    Environment = var.environment
  })
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "trustmoss-${var.environment}-redis-subnets"
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, {
    Name        = "trustmoss-${var.environment}-redis-subnets"
    Environment = var.environment
  })
}

resource "aws_security_group" "redis" {
  name        = "trustmoss-${var.environment}-redis-sg"
  description = "Controls access to ElastiCache Redis"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis from permitted compute security groups"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name        = "trustmoss-${var.environment}-redis-sg"
    Environment = var.environment
  })
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "trustmoss-${var.environment}-cache"
  description                   = "Redis cluster for TrustMoss session store and cache"
  node_type                     = var.redis_node_type
  num_cache_clusters            = var.redis_num_cache_nodes
  port                          = 6379
  parameter_group_name          = "default.redis7"
  subnet_group_name             = aws_elasticache_subnet_group.redis.name
  security_group_ids            = [aws_security_group.redis.id]
  at_rest_encryption_enabled    = true
  transit_encryption_enabled   = true
  automatic_failover_enabled    = var.redis_num_cache_nodes > 1 ? true : false

  tags = merge(var.tags, {
    Name        = "trustmoss-${var.environment}-redis"
    Environment = var.environment
  })
}
