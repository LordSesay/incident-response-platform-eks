#!/bin/bash
# DevOps EKS Pipeline Setup Script
# This script automates the initial setup of the EKS infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
# Defaults match infrastructure/variables.tf.
AWS_REGION=${AWS_REGION:-"us-east-1"}
CLUSTER_NAME=${CLUSTER_NAME:-"incident-response-eks"}
TERRAFORM_DIR="infrastructure"
PLAN_FILE="terraform.tfplan"

echo -e "${GREEN}🚀 DevOps EKS Pipeline Setup${NC}"
echo "=================================="

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Initialize Terraform
init_terraform() {
    echo -e "${YELLOW}🔧 Initializing Terraform...${NC}"
    cd $TERRAFORM_DIR
    if [[ ! -f backend.hcl ]]; then
        echo -e "${RED}❌ $TERRAFORM_DIR/backend.hcl not found; copy backend.hcl.example and set the state bucket${NC}"
        exit 1
    fi
    terraform init -backend-config=backend.hcl
    cd ..
    echo -e "${GREEN}✅ Terraform initialized${NC}"
}

# Plan infrastructure
plan_infrastructure() {
    echo -e "${YELLOW}📋 Planning infrastructure...${NC}"
    cd $TERRAFORM_DIR
    terraform plan -var="aws_region=$AWS_REGION" -var="eks_cluster_name=$CLUSTER_NAME" -out="$PLAN_FILE"
    cd ..
    echo -e "${GREEN}✅ Infrastructure plan complete${NC}"
}

# Apply infrastructure
apply_infrastructure() {
    echo -e "${YELLOW}🏗️  Applying infrastructure...${NC}"
    cd $TERRAFORM_DIR
    # Apply exactly the plan that was reviewed; a saved plan needs no -var flags.
    terraform apply "$PLAN_FILE"
    rm -f "$PLAN_FILE"
    cd ..
    echo -e "${GREEN}✅ Infrastructure applied${NC}"
}

# Configure kubectl
configure_kubectl() {
    echo -e "${YELLOW}⚙️  Configuring kubectl...${NC}"
    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"
    echo -e "${GREEN}✅ kubectl configured${NC}"
}

# Verify cluster
verify_cluster() {
    echo -e "${YELLOW}🔍 Verifying cluster...${NC}"
    kubectl get nodes
    kubectl get pods --all-namespaces
    echo -e "${GREEN}✅ Cluster verification complete${NC}"
}

# Main execution
main() {
    check_prerequisites
    init_terraform
    plan_infrastructure
    
    # Ask for confirmation before applying
    echo -e "${YELLOW}⚠️  Ready to create infrastructure. Continue? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        apply_infrastructure
        configure_kubectl
        verify_cluster
        
        echo -e "${GREEN}🎉 Setup complete!${NC}"
        echo "Your EKS cluster is ready. You can now deploy applications using:"
        echo "kubectl apply -f application/k8s/"
    else
        echo -e "${YELLOW}Setup cancelled${NC}"
    fi
}

# Run main function
main "$@"