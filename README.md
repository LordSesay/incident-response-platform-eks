# incident-response-platform-eks

## Overview

incident-response-platform-eks is a cloud-native internal operations platform built to standardize alert intake, classify incident severity, and expose incident data to responders through APIs and a dashboard.

The project demonstrates how a multi-service platform can be deployed to Amazon EKS using GitHub Actions for CI/CD, Terraform for infrastructure provisioning, Docker for containerization, and CloudWatch / Prometheus for observability.

This is not a generic web app deployment demo.
It is a portfolio project designed to simulate how platform and DevOps engineers support internal engineering operations at enterprise scale.

---

## Problem Statement

Engineering teams often receive alerts from multiple systems such as infrastructure monitors, application logs, and external integrations. In many environments, these alerts are inconsistent, noisy, and difficult to triage quickly.

Common operational problems include:

- Alert fatigue caused by high volumes of unstructured events
- Inconsistent severity classification between teams
- Delayed response due to fragmented tooling
- Lack of centralized visibility into active incidents
- Manual deployment workflows that increase operational risk

The goal of this project is to create an internal platform that centralizes incoming alerts, classifies incident severity, stores normalized incident records, and provides a consistent deployment and observability model on Kubernetes.

---

## Solution

This platform includes:

- **Alert Ingestion API** to receive incoming incident or alert payloads
- **Classifier Service** to normalize alerts and assign severity / ownership
- **Incident API** to retrieve and manage incident records
- **Operations Dashboard** to visualize active incidents and platform health
- **Amazon EKS** for Kubernetes orchestration
- **Terraform** for infrastructure as code
- **GitHub Actions** for automated build, test, push, and deployment workflows
- **Amazon ECR** for container image storage
- **CloudWatch and Prometheus** for logs and metrics

---

## Architecture

```
Developer Push
     |
     v
GitHub Repository
     |
     v
GitHub Actions CI/CD
  - test services
  - build Docker images
  - push images to ECR
  - deploy manifests to EKS
     |
     v
Amazon EKS Cluster
  - ingestion-api
  - classifier-service
  - incident-api
  - dashboard
     |
     v
DynamoDB / Incident Store
     |
     v
CloudWatch + Prometheus + Grafana
```

---

## Why EKS

Kubernetes is justified in this project because the platform is composed of multiple independently deployable services with different runtime behaviors.

EKS provides:

- Rolling deployments for safer releases
- Service discovery between internal services
- Horizontal scaling for ingestion-heavy workloads
- Self-healing through health probes and pod restarts
- A realistic platform for observability, RBAC, and workload separation

This makes the project meaningfully different from simpler ECS-based application deployments.

---

## Core Services

### 1. ingestion-api

Receives incoming alerts through REST endpoints.

Example responsibilities:
- Validate payloads
- Assign request IDs
- Publish or persist raw alert data
- Forward normalized records for classification

### 2. classifier-service

Applies incident classification rules.

Example responsibilities:
- Severity mapping
- Incident priority assignment
- Team ownership tagging
- Status initialization

### 3. incident-api

Exposes incident data to users and internal tools.

Example endpoints:
- `GET /incidents`
- `GET /incidents/{id}`
- `PATCH /incidents/{id}`

### 4. dashboard

Internal interface for responders to review incidents, status, and metrics.

---

## Repository Structure

```
incident-response-platform-eks/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── application/
│   ├── ingestion-api/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── classifier-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── incident-api/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── dashboard/
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── package.json
│   └── k8s/
│       ├── namespace.yaml
│       ├── ingestion-api.yaml
│       ├── classifier-service.yaml
│       ├── incident-api.yaml
│       ├── dashboard.yaml
│       ├── configmap.yaml
│       ├── secrets.yaml
│       └── ingress.yaml
├── infrastructure/
│   ├── modules/
│   │   ├── vpc/
│   │   ├── eks/
│   │   ├── ecr/
│   │   ├── iam/
│   │   └── monitoring/
│   ├── environments/
│   │   ├── dev/
│   │   └── prod/
│   └── main.tf
├── docs/
│   ├── architecture.md
│   ├── diagrams/
│   ├── runbooks/
│   ├── screenshots/
│   └── learning-notes.md
├── scripts/
│   ├── bootstrap.sh
│   ├── deploy.sh
│   └── smoke-test.sh
├── README.md
└── QUICKSTART.md
```

---

## CI/CD Workflow

The deployment pipeline is powered by GitHub Actions.

High-level workflow:

1. Developer pushes code to GitHub
2. Workflow runs tests for changed services
3. Docker images are built and tagged
4. Images are pushed to Amazon ECR
5. Kubernetes manifests are updated or applied
6. Workloads are deployed to Amazon EKS
7. Smoke tests validate deployment success

This pipeline removes manual deployment steps and creates a repeatable release process.

---

## Infrastructure

Terraform provisions the AWS environment required to run the platform, including:

- VPC and networking
- EKS cluster and node groups
- ECR repositories
- IAM roles and policies
- Security groups
- Monitoring components
- Optional DNS / ingress support

---

## Observability

The platform includes observability at both the infrastructure and workload layers.

**Logging**
- CloudWatch for centralized application and infrastructure logs

**Metrics**
- Prometheus for Kubernetes and service metrics
- Grafana dashboards for visualization

**Health validation**
- Liveness and readiness probes
- Deployment rollout checks
- Smoke testing after deployment

---

## Security

Security controls demonstrated in this project include:

- IAM least privilege for AWS resources
- Kubernetes RBAC
- Namespace isolation
- Secret handling for service configuration
- Containerized workloads with controlled deployment paths
- Optional image scanning and policy enforcement

---

## Local Development

### Prerequisites

- AWS CLI configured
- Terraform >= 1.0
- kubectl
- Docker
- Python 3.11+
- GitHub repository secrets configured for CI/CD

### Clone the repository

```bash
git clone https://github.com/LordSesay/incident-response-platform-eks.git
cd incident-response-platform-eks
```

### Provision infrastructure

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

### Configure kubectl

```bash
aws eks update-kubeconfig --region us-east-1 --name incident-response-eks
```

### Deploy workloads

```bash
kubectl apply -f application/k8s/
```

---

## Real Execution Goals

This project is designed to demonstrate real platform-engineering experience, including:

- Designing multi-service containerized systems
- Provisioning repeatable AWS infrastructure with Terraform
- Automating deployments with GitHub Actions
- Deploying and operating workloads on Kubernetes
- Implementing monitoring, logging, and rollout validation
- Documenting operational lessons learned

---

## Challenges I Expect to Solve

As this project evolves, key engineering challenges will include:

- GitHub Actions authentication to AWS
- ECR image versioning and deployment traceability
- Service-to-service communication in Kubernetes
- Readiness and liveness probe tuning
- Terraform dependency management
- Scaling and rollout behavior under load
- Observability and debugging across services

This section will be updated with real troubleshooting notes as the build progresses.

---

## Future Enhancements

Possible future improvements include:

- Helm chart packaging
- ArgoCD for GitOps-based delivery
- Incident notification integrations
- SQS or SNS-based event flow
- Authentication for dashboard users
- Advanced routing and ingress controls
- Multi-environment promotion strategy

---

## Author

**LordSesay**
