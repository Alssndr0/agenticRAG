output "cluster_name" {
  value = aws_eks_cluster.this.name
}

output "kubeconfig" {
  value = aws_eks_cluster.this.endpoint
  description = "K8s API endpoint (use with aws eks update-kubeconfig)"
}