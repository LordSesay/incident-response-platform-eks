@echo off
REM DevOps EKS Pipeline Setup Script for Windows
REM This script automates the initial setup of the EKS infrastructure

echo.
echo 🚀 DevOps EKS Pipeline Setup
echo ==================================

REM Configuration (defaults match infrastructure\variables.tf)
if not defined AWS_REGION set AWS_REGION=us-east-1
if not defined CLUSTER_NAME set CLUSTER_NAME=incident-response-eks
set TERRAFORM_DIR=infrastructure
set PLAN_FILE=terraform.tfplan

echo.
echo 📋 Checking prerequisites...

REM Check if AWS CLI is installed
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ AWS CLI is not installed
    exit /b 1
)

REM Check if Terraform is installed
terraform --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Terraform is not installed
    exit /b 1
)

REM Check if kubectl is installed
kubectl version --client >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ kubectl is not installed
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ AWS credentials not configured
    exit /b 1
)

echo ✅ All prerequisites met

echo.
echo 🔧 Initializing Terraform...
cd %TERRAFORM_DIR%
if not exist backend.hcl (
    echo ❌ %TERRAFORM_DIR%\backend.hcl not found; copy backend.hcl.example and set the state bucket
    cd ..
    exit /b 1
)
terraform init -backend-config=backend.hcl
if %errorlevel% neq 0 (
    echo ❌ Terraform init failed
    cd ..
    exit /b 1
)
cd ..
echo ✅ Terraform initialized

echo.
echo 📋 Planning infrastructure...
cd %TERRAFORM_DIR%
terraform plan -var="aws_region=%AWS_REGION%" -var="eks_cluster_name=%CLUSTER_NAME%" -out="%PLAN_FILE%"
if %errorlevel% neq 0 (
    echo ❌ Terraform plan failed
    cd ..
    exit /b 1
)
cd ..
echo ✅ Infrastructure plan complete

echo.
echo ⚠️  Ready to create infrastructure. Continue? (y/N)
set /p response=
REM Inside a parenthesised block %errorlevel% is expanded once at parse time,
REM so the checks below use "if errorlevel 1", which is evaluated at runtime.
if /i "%response%"=="y" (
    echo.
    echo 🏗️  Applying infrastructure...
    cd %TERRAFORM_DIR%
    terraform apply "%PLAN_FILE%"
    if errorlevel 1 (
        echo ❌ Terraform apply failed
        cd ..
        exit /b 1
    )
    del "%PLAN_FILE%"
    cd ..
    echo ✅ Infrastructure applied

    echo.
    echo ⚙️  Configuring kubectl...
    aws eks update-kubeconfig --region %AWS_REGION% --name %CLUSTER_NAME%
    if errorlevel 1 (
        echo ❌ kubectl configuration failed
        exit /b 1
    )
    echo ✅ kubectl configured

    echo.
    echo 🔍 Verifying cluster...
    kubectl get nodes
    kubectl get pods --all-namespaces
    echo ✅ Cluster verification complete

    echo.
    echo 🎉 Setup complete!
    echo Your EKS cluster is ready. You can now deploy applications using:
    echo kubectl apply -f application/k8s/
) else (
    echo Setup cancelled
)

pause