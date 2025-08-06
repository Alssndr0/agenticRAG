# EKS Cluster with Terraform - Setup Guide

This Terraform configuration creates a production-ready Amazon EKS (Elastic Kubernetes Service).

### Core Infrastructure:
- **VPC**: Private network with public and private subnets across 2 availability zones
- **EKS Cluster**: Managed Kubernetes cluster with logging enabled
- **Worker Nodes**: Auto-scaling group of EC2 instances in private subnets
- **Security Groups**: Proper network security between cluster components
- **IAM Roles**: Required permissions for EKS cluster and worker nodes
- **ECR Repository**: Private Docker registry for application images



## Prerequisites

1. **AWS CLI** installed and configured:
```bash
aws configure
```

2. **Terraform** installed (version 1.0+):
```bash
# On macOS
brew install terraform
# On Ubuntu
sudo apt-get install terraform
```

3. **kubectl** installed:
```bash
# On macOS
brew install kubectl

# On Ubuntu
sudo apt-get install kubectl
```

## Quick Start

**Terraform**:
```bash
# initialise
terraform init
# plan
terraform plan
# deploy
terraform apply
```

### Configure kubectl

After deployment completes, configure kubectl to access your cluster:
```bash
aws eks update-kubeconfig --region eu-west-1 --name traydstream-eks
```

Verify connection:
```bash
kubectl get nodes
```

### Deploy Your Application

1. **Build and push Docker image**:
   ```bash
   # Login to ECR (use the command from terraform output)
   aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <ECR_URL>
   
   # Build your Docker image
   docker build -t your-app .
   
   # Tag for ECR
   docker tag your-app:latest <ECR_URL>:latest
   
   # Push to ECR
   docker push <ECR_URL>:latest
   ```

2. **Apply Kubernetes Deployment**:
   ```bash
   kubectl apply -f app-deployment.yaml
   ```

3. **Get your application URL**:
   ```bash
   kubectl get service your-app-service
   ```

## 💰 Cost Optimization

### Development Environment:
- Use `t3.small` instances
- Set `min_capacity = 1, desired_capacity = 1`
- Use Spot instances (modify the configuration)

### Production Environment:
- Use `t3.medium` or larger instances
- Set `min_capacity = 3` for high availability
- Enable cluster autoscaling

## 🔧 Configuration Options

### Instance Types:
```hcl
# Cost-effective for development
instance_types = ["t3.small"]

# Balanced for production
instance_types = ["t3.medium"]

# High-performance applications
instance_types = ["c5.large", "c5.xlarge"]
```

### Scaling Configuration:
```hcl
# Auto-scaling based on demand
min_capacity     = 2
max_capacity     = 10
desired_capacity = 3
```

## Monitoring and Troubleshooting

### View cluster status:
```bash
kubectl get nodes
kubectl get pods --all-namespaces
```

### Check cluster logs:
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/eks/traydstream-eks"
```

## Cleanup

To avoid ongoing charges, destroy the infrastructure when not needed:

```bash
# Delete any LoadBalancer services first
kubectl delete service --all

# Destroy Terraform resources
terraform destroy
```

## Next Steps

1. **Install AWS Load Balancer Controller** for advanced load balancing
2. **Set up monitoring** with Prometheus and Grafana
3. **Configure autoscaling** with Cluster Autoscaler
4. **Implement CI/CD** with AWS CodePipeline or GitHub Actions
5. **Add SSL certificates** with AWS Certificate Manager
