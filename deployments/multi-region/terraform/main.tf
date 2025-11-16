terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    bucket         = "siem-terraform-state"
    key            = "multi-region/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

# Variables
variable "region" {
  description = "AWS region for deployment"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "siem-cluster"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = []
}

# Locals
locals {
  common_tags = {
    Environment = var.environment
    Project     = "Enterprise-SIEM"
    ManagedBy   = "Terraform"
    Region      = var.region
  }

  azs = length(var.availability_zones) > 0 ? var.availability_zones : [
    "${var.region}a",
    "${var.region}b",
    "${var.region}c"
  ]
}

# Provider
provider "aws" {
  region = var.region

  default_tags {
    tags = local.common_tags
  }
}

# VPC Module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = local.azs
  private_subnets = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 48)]
  database_subnets = [for k, v in local.azs : cidrsubnet(var.vpc_cidr, 8, k + 64)]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  eks_managed_node_groups = {
    # General purpose nodes
    general = {
      min_size     = 3
      max_size     = 20
      desired_size = 5

      instance_types = ["m5.2xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "general"
      }

      tags = {
        NodeGroup = "general"
      }
    }

    # High memory nodes for Elasticsearch
    elasticsearch = {
      min_size     = 3
      max_size     = 10
      desired_size = 6

      instance_types = ["r5.4xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "elasticsearch"
      }

      taints = [{
        key    = "dedicated"
        value  = "elasticsearch"
        effect = "NoSchedule"
      }]

      tags = {
        NodeGroup = "elasticsearch"
      }
    }

    # Kafka nodes
    kafka = {
      min_size     = 3
      max_size     = 12
      desired_size = 9

      instance_types = ["i3.2xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        role = "kafka"
      }

      taints = [{
        key    = "dedicated"
        value  = "kafka"
        effect = "NoSchedule"
      }]

      tags = {
        NodeGroup = "kafka"
      }
    }
  }

  tags = {
    Name = var.cluster_name
  }
}

# RDS PostgreSQL
module "postgres" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.cluster_name}-postgres"

  engine               = "postgres"
  engine_version       = "15.4"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.r5.2xlarge"

  allocated_storage     = 1000
  max_allocated_storage = 5000
  storage_encrypted     = true
  storage_type          = "gp3"

  db_name  = "siem"
  username = "siem_admin"
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.postgres.id]

  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  create_cloudwatch_log_group     = true

  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.cluster_name}-postgres-final-snapshot"

  performance_insights_enabled = true
  performance_insights_retention_period = 7

  parameters = [
    {
      name  = "max_connections"
      value = "1000"
    },
    {
      name  = "shared_buffers"
      value = "16384" # 16GB
    },
    {
      name  = "effective_cache_size"
      value = "49152" # 48GB
    },
    {
      name  = "maintenance_work_mem"
      value = "2097152" # 2GB
    },
    {
      name  = "wal_buffers"
      value = "2048" # 16MB
    }
  ]

  tags = {
    Name = "${var.cluster_name}-postgres"
  }
}

# Security Group for PostgreSQL
resource "aws_security_group" "postgres" {
  name        = "${var.cluster_name}-postgres-sg"
  description = "Security group for PostgreSQL RDS"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "PostgreSQL from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-postgres-sg"
  }
}

# ElastiCache Redis
module "redis" {
  source  = "terraform-aws-modules/elasticache/aws"
  version = "~> 1.0"

  cluster_id               = "${var.cluster_name}-redis"
  engine                   = "redis"
  engine_version           = "7.0"
  node_type                = "cache.r5.2xlarge"
  num_cache_nodes          = 6
  parameter_group_name     = "default.redis7.cluster.on"
  port                     = 6379
  subnet_group_name        = aws_elasticache_subnet_group.redis.name
  security_group_ids       = [aws_security_group.redis.id]

  automatic_failover_enabled = true
  multi_az_enabled          = true

  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"

  tags = {
    Name = "${var.cluster_name}-redis"
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.cluster_name}-redis-subnet"
  subnet_ids = module.vpc.private_subnets

  tags = {
    Name = "${var.cluster_name}-redis-subnet"
  }
}

resource "aws_security_group" "redis" {
  name        = "${var.cluster_name}-redis-sg"
  description = "Security group for Redis ElastiCache"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Redis from VPC"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-redis-sg"
  }
}

# S3 Bucket for Cold Storage
module "s3_cold_storage" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "~> 3.0"

  bucket = "${var.cluster_name}-cold-storage-${var.region}"
  acl    = "private"

  versioning = {
    enabled = true
  }

  server_side_encryption_configuration = {
    rule = {
      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  lifecycle_rule = [
    {
      id      = "transition-to-glacier"
      enabled = true

      transition = [
        {
          days          = 90
          storage_class = "GLACIER"
        },
        {
          days          = 365
          storage_class = "DEEP_ARCHIVE"
        }
      ]

      expiration = {
        days = 2555 # 7 years
      }
    }
  ]

  tags = {
    Name = "${var.cluster_name}-cold-storage"
  }
}

# Outputs
output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "postgres_endpoint" {
  description = "PostgreSQL endpoint"
  value       = module.postgres.db_instance_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.cluster_cache_nodes
  sensitive   = true
}

output "s3_bucket" {
  description = "S3 cold storage bucket"
  value       = module.s3_cold_storage.s3_bucket_id
}
