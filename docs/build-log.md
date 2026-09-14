# Troubleshooting Guide

## 🔧 Common Issues and Solutions

### 1. Terraform Issues

#### Issue: "Error: configuring Terraform AWS Provider"
**Symptoms:**
```
Error: configuring Terraform AWS Provider: no valid credential sources for Terraform AWS Provider found
```

**Solution:**
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"
```

#### Issue: "Error: creating EKS Cluster: InvalidParameterException"
**Symptoms:**
```
Error: creating EKS Cluster: InvalidParameterException: The provided subnets must be in at least 2 different availability zones
```

**Solution:**
- Ensure subnets are created in different AZs
- Check availability zone data source in Terraform

### 2. EKS Cluster Issues

#### Issue: "error: You must be logged in to the server (Unauthorized)"
**Symptoms:**
```bash
kubectl get nodes
error: You must be logged in to the server (Unauthorized)
```

**Solution:**
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name devops-eks-cluster

# Verify AWS identity
aws sts get-caller-identity
```

#### Issue: "Nodes not joining cluster"
**Symptoms:**
- Nodes appear in EC2 but not in `kubectl get nodes`
- Node group status shows "CREATE_FAILED"

**Solution:**
1. Check IAM roles and policies
2. Verify security group rules
3. Check subnet tags:
```bash
# Required tags for EKS subnets
kubernetes.io/cluster/devops-eks-cluster = shared
```

### 3. Application Deployment Issues

#### Issue: "ImagePullBackOff" error
**Symptoms:**
```bash
kubectl get pods
NAME                          READY   STATUS             RESTARTS   AGE
devops-app-xxx                0/1     ImagePullBackOff   0          2m
```

**Solution:**
```bash
# Check if image exists in ECR
aws ecr describe-images --repository-name devops-eks-pipeline

# Update deployment with correct image URI
kubectl edit deployment devops-app
```

#### Issue: "CrashLoopBackOff" error
**Symptoms:**
```bash
kubectl get pods
NAME                          READY   STATUS             RESTARTS   AGE
devops-app-xxx                0/1     CrashLoopBackOff   3          5m
```

**Solution:**
```bash
# Check pod logs
kubectl logs devops-app-xxx

# Check pod events
kubectl describe pod devops-app-xxx

# Common fixes:
# 1. Fix application startup issues
# 2. Adjust resource limits
# 3. Fix health check endpoints
```

### 4. Networking Issues

#### Issue: "Service not accessible from internet"
**Symptoms:**
- Service created but not accessible via LoadBalancer
- LoadBalancer stuck in "pending" state

**Solution:**
```bash
# Check service status
kubectl get svc

# Check LoadBalancer events
kubectl describe svc devops-app-service

# Verify security groups allow traffic on port 80/443
# Check subnet tags for LoadBalancer
```

#### Issue: "Pod-to-pod communication failing"
**Symptoms:**
- Pods can't communicate with each other
- DNS resolution issues

**Solution:**
```bash
# Check CoreDNS pods
kubectl get pods -n kube-system | grep coredns

# Test DNS resolution
kubectl run test-pod --image=busybox --rm -it -- nslookup kubernetes.default

# Check network policies
kubectl get networkpolicies
```

### 5. CI/CD Pipeline Issues

#### Issue: "GitHub Actions failing on AWS authentication"
**Symptoms:**
```
Error: Could not load credentials from any providers
```

**Solution:**
1. Add AWS credentials to GitHub Secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

2. Or use OIDC (recommended):
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::ACCOUNT:role/GitHubActionsRole
    aws-region: us-west-2
```

#### Issue: "Docker build failing in GitHub Actions"
**Symptoms:**
```
Error: Cannot connect to the Docker daemon
```

**Solution:**
- Ensure using `ubuntu-latest` runner
- Check Dockerfile syntax
- Verify build context

### 6. Resource Issues

#### Issue: "Insufficient capacity" error
**Symptoms:**
```
Error: creating EKS Node Group: ResourceLimitExceeded: You have requested more instances (2) than your current instance limit of 0
```

**Solution:**
```bash
# Request service limit increase in AWS Console
# Or use different instance types
# Check current limits:
aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A
```

#### Issue: "Pods stuck in Pending state"
**Symptoms:**
```bash
kubectl get pods
NAME                          READY   STATUS    RESTARTS   AGE
devops-app-xxx                0/1     Pending   0          5m
```

**Solution:**
```bash
# Check pod events
kubectl describe pod devops-app-xxx

# Common causes:
# 1. Insufficient resources
# 2. Node selector issues
# 3. Taints and tolerations
# 4. PVC mounting issues

# Check node resources
kubectl top nodes
kubectl describe nodes
```

## 🔍 Debugging Commands

### Cluster Information
```bash
# Cluster info
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods --all-namespaces

# Check cluster health
kubectl get componentstatuses
```

### Application Debugging
```bash
# Pod logs
kubectl logs <pod-name> -f
kubectl logs <pod-name> --previous

# Pod shell access
kubectl exec -it <pod-name> -- /bin/sh

# Port forwarding for testing
kubectl port-forward <pod-name> 8080:3000
```

### Network Debugging
```bash
# Service endpoints
kubectl get endpoints

# Network policies
kubectl get networkpolicies

# DNS testing
kubectl run test-pod --image=busybox --rm -it -- nslookup <service-name>
```

### Resource Monitoring
```bash
# Resource usage
kubectl top nodes
kubectl top pods

# Resource quotas
kubectl get resourcequotas
kubectl describe resourcequotas
```

## 📞 Getting Help

### AWS Support
- AWS Support Center
- AWS Forums
- AWS Documentation

### Kubernetes Community
- Kubernetes Slack
- Stack Overflow (kubernetes tag)
- GitHub Issues

### Terraform
- Terraform Registry
- HashiCorp Forums
- Terraform GitHub Issues

## 🚨 Emergency Procedures

### Cluster Recovery
1. Check cluster status in AWS Console
2. Verify node group health
3. Check CloudTrail for recent changes
4. Consider cluster recreation if necessary

### Data Recovery
1. Check backup status
2. Restore from latest backup
3. Verify data integrity
4. Update DNS/load balancer if needed

### Rollback Procedures
```bash
# Application rollback
kubectl rollout undo deployment/devops-app

# Infrastructure rollback
cd infrastructure
terraform plan -destroy
terraform apply
```

---

Remember: Always check logs first, then events, then describe resources for detailed information.