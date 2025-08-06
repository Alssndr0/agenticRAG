# ========================================
# Example terraform.tfvars file
# Copy this to terraform.tfvars and customize as needed
# ========================================

# Basic Configuration
region       = "eu-west-1"
cluster_name = "traydstream-eks"
environment  = "dev"

# Kubernetes Version (check AWS documentation for available versions)
kubernetes_version = "1.28"

# Worker Node Configuration
instance_types    = ["t3.medium"]  # Minimum recommended for EKS
min_capacity      = 1
max_capacity      = 5
desired_capacity  = 2

# Network Configuration
vpc_cidr = "10.0.0.0/16"

# Features
enable_cluster_logging = true

# Additional Tags (optional)
additional_tags = {
  Project     = "TraydStream"
  Owner       = "Alessandro"
  Environment = "Development"
}
