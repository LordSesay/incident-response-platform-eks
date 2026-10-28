#!/bin/bash
# DevOps EKS Pipeline Cleanup Script
# This script safely destroys the EKS infrastructure

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

echo -e "${RED}🧹 DevOps EKS Pipeline Cleanup${NC}"
echo "=================================="

# Warning message
warning_message() {
    echo -e "${RED}⚠️  WARNING: This will destroy all infrastructure!${NC}"
    echo -e "${RED}This action cannot be undone.${NC}"
    echo ""
    echo "This will delete:"
    echo "- EKS Cluster: $CLUSTER_NAME"
    echo "- VPC and all networking components"
    echo "- EC2 instances (worker nodes)"
    echo "- Load balancers and associated resources"
    echo ""
}

# Remove applications from cluster
cleanup_applications() {
    echo -e "${YELLOW}🗑️  Removing applications from cluster...${NC}"
    
    # Target the named cluster explicitly rather than whatever context is current.
    # update-kubeconfig names the context after the cluster ARN.
    CLUSTER_ARN=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query cluster.arn --output text 2>/dev/null || true)
    if [[ -n "$CLUSTER_ARN" ]] && kubectl --context "$CLUSTER_ARN" cluster-info &> /dev/null; then
        kubectl --context "$CLUSTER_ARN" delete -f application/k8s/ --ignore-not-found=true --wait=true

        echo -e "${GREEN}✅ Applications removed${NC}"
    else
        echo -e "${YELLOW}⚠️  Cluster not accessible, skipping application cleanup${NC}"
    fi
}

# Destroy infrastructure
destroy_infrastructure() {
    echo -e "${YELLOW}💥 Destroying infrastructure...${NC}"
    cd $TERRAFORM_DIR
    terraform destroy -var="aws_region=$AWS_REGION" -var="eks_cluster_name=$CLUSTER_NAME" -auto-approve
    cd ..
    echo -e "${GREEN}✅ Infrastructure destroyed${NC}"
}

# Clean up kubectl config
cleanup_kubectl() {
    echo -e "${YELLOW}🧹 Cleaning up kubectl config...${NC}"
    # kubectl does not expand wildcards, so use the ARN captured before destroy.
    if [[ -n "${CLUSTER_ARN:-}" ]]; then
        kubectl config delete-context "$CLUSTER_ARN" 2>/dev/null || true
        kubectl config delete-cluster "$CLUSTER_ARN" 2>/dev/null || true
        kubectl config unset "users.$CLUSTER_ARN" 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ kubectl config cleaned${NC}"
}

# Verify cleanup
verify_cleanup() {
    echo -e "${YELLOW}🔍 Verifying cleanup...${NC}"
    
    # Check if cluster still exists
    if aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" &> /dev/null; then
        echo -e "${RED}❌ Cluster still exists${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ Cluster successfully deleted${NC}"
    fi
}

# Main execution
main() {
    warning_message
    
    # Ask for confirmation
    echo -e "${RED}Are you sure you want to proceed? Type 'DELETE' to confirm:${NC}"
    read -r response
    
    if [[ "$response" == "DELETE" ]]; then
        cleanup_applications
        destroy_infrastructure
        cleanup_kubectl
        verify_cleanup
        
        echo -e "${GREEN}🎉 Cleanup complete!${NC}"
        echo "All infrastructure has been destroyed."
    else
        echo -e "${YELLOW}Cleanup cancelled${NC}"
    fi
}

# Run main function
main "$@"