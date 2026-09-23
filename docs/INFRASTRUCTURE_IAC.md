# Infrastructure as Code (IaC) — TrustMoss

This directory (`terraform/`) defines the complete Infrastructure as Code (IaC) for TrustMoss using HashiCorp Terraform. It transitions TrustMoss deployment from raw shell scripts and local Docker Compose files to versioned, reproducible, enterprise-grade cloud topologies.

---

## 1. Directory Structure

```
terraform/
├── versions.tf                        # Root Terraform engine & provider constraints
├── modules/
│   ├── networking/                    # VPC, Public/Private subnets, NAT Gateway, Routing
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/                      # AWS RDS PostgreSQL (Multi-AZ) & ElastiCache Redis
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── compute/                       # AWS ECS Fargate, ALB, Target Groups, ECR, CloudWatch
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── staging/                       # Non-production isolated environment (cost-optimized)
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── terraform.tfvars.example
    └── production/                    # Production HA environment (Multi-AZ, deletion-protected)
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars.example
```

---

## 2. Environment Specifications

| Feature | Staging | Production |
| :--- | :--- | :--- |
| **VPC CIDR** | `10.10.0.0/16` | `10.20.0.0/16` |
| **RDS Instance Class** | `db.t4g.micro` | `db.t4g.small` |
| **RDS Multi-AZ** | Disabled (`false`) | Enabled (`true`) |
| **RDS Backups** | 3 days retention | 14 days retention |
| **RDS Deletion Protection** | Disabled (`false`) | Enabled (`true`) |
| **Redis Cache Nodes** | 1 (`cache.t4g.micro`) | 2 (`cache.t4g.small`, Auto-failover) |
| **ECS Tasks Desired Count** | 1 API, 1 Web | 3 API, 3 Web (with horizontal scaling) |
| **CloudWatch Log Retention**| 14 days | 90 days |

---

## 3. Remote State Setup (AWS S3 + DynamoDB)

To prevent concurrent state modifications and secure sensitive values, configure an S3 bucket with server-side encryption and DynamoDB table locking:

```bash
# S3 state bucket
aws s3api create-bucket \
    --bucket trustmoss-terraform-state-production \
    --region us-east-1

aws s3api put-bucket-versioning \
    --bucket trustmoss-terraform-state-production \
    --versioning-configuration Status=Enabled

# DynamoDB state lock
aws dynamodb create-table \
    --table-name trustmoss-terraform-locks-production \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

Uncomment the `backend "s3"` block in `terraform/environments/staging/main.tf` and `terraform/environments/production/main.tf`.

---

## 4. Local Execution & Planning

To plan or apply changes manually:

```bash
cd terraform/environments/staging
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform plan -out=tfplan
# terraform apply tfplan
```
