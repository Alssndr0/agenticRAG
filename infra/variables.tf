# ========================================
# EKS Cluster Outputs
# ========================================

# EKS Cluster Name
output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = aws_eks_cluster.this.name
}

# EKS Cluster Endpoint
output "cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = aws_eks_cluster.this.endpoint
}

# EKS Cluster Security Group ID
output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

# EKS Cluster IAM Role ARN
output "cluster_iam_role_arn" {
  description = "IAM role ARN of the EKS cluster"
  value       = aws_eks_cluster.this.role_arn
}

# EKS Cluster Version
output "cluster_version" {
  description = "Version of Kubernetes running on the EKS cluster"
  value       = aws_eks_cluster.this.version
}

# ========================================
# VPC and Network Outputs
# ========================================

# VPC ID
output "vpc_id" {
  description = "ID of the VPC where the cluster is deployed"
  value       = aws_vpc.this.id
}

# Public Subnet IDs
output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

# Private Subnet IDs
output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

# ========================================
# Node Group Outputs
# ========================================

# Node Group Name
output "node_group_name" {
  description = "Name of the EKS node group"
  value       = aws_eks_node_group.general.node_group_name
}

# Node Group Status
output "node_group_status" {
  description = "Status of the EKS node group"
  value       = aws_eks_node_group.general.status
}

# Node Group IAM Role ARN
output "node_group_iam_role_arn" {
  description = "IAM role ARN of the EKS node group"
  value       = aws_eks_node_group.general.node_role_arn
}

# ========================================
# ECR Repository Outputs
# ========================================

# ECR Repository URL
output "ecr_repository_url" {
  description = "URL of the ECR repository for your Docker images"
  value       = aws_ecr_repository.app.repository_url
}

# ECR Repository ARN
output "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.app.arn
}

# ========================================
# kubectl Configuration Command
# ========================================

# Command to configure kubectl
output "kubectl_config_command" {
  description = "Command to configure kubectl to access the cluster"
  value       = "aws eks update-kubeconfig --region ${var.region} --name ${aws_eks_cluster.this.name}"
}

# ========================================
# Docker Login Command for ECR
# ========================================

# Command to login to ECR
output "ecr_login_command" {
  description = "Command to login to ECR for pushing Docker images"
  value       = "aws ecr get-login-password --region ${var.region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app.repository_url}"
}