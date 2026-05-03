## Cloud Provider

| Provider | Primary Services              |
| -------- | ----------------------------- |
| AWS      | EKS, RDS, S3, Lambda, SQS     |
| GCP      | GKE, Cloud SQL, Cloud Storage |
| Azure    | AKS, Azure SQL, Blob Storage  |

---

## Infrastructure as Code

### Terraform (Preferred)

#### Project Structure

```
/terraform
  /modules
    /vpc
      main.tf
      variables.tf
      outputs.tf
    /eks
    /rds
  /environments
    /dev
      main.tf
      terraform.tfvars
    /staging
    /prod
  backend.tf
  providers.tf
  versions.tf
```

#### State Management

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "env/prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

#### Module Pattern

```hcl
# modules/eks/main.tf
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = var.kubernetes_version

  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  eks_managed_node_groups = {
    default = {
      min_size     = var.min_nodes
      max_size     = var.max_nodes
      desired_size = var.desired_nodes

      instance_types = var.instance_types
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = var.tags
}

# modules/eks/variables.tf
variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster"
}

variable "kubernetes_version" {
  type        = string
  default     = "1.28"
  description = "Kubernetes version"
}

# modules/eks/outputs.tf
output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}
```

#### Best Practices

```hcl
# Always use version constraints
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Use data sources for existing resources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Use locals for computed values
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  name_prefix = "${var.project}-${var.environment}"
}

# Always tag resources
resource "aws_instance" "example" {
  # ...

  tags = merge(var.common_tags, {
    Name        = "${local.name_prefix}-instance"
    Environment = var.environment
    ManagedBy   = "terraform"
  })
}
```

---

