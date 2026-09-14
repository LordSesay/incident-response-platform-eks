# Architecture and implementation boundary

## Implemented application

The ingestion FastAPI process validates alert field types, generates a UUID and UTC creation time, maps severity and service name to priority and team, then writes one incident to DynamoDB. The incident FastAPI process scans incidents (including subsequent scan pages), filters by status/severity, and retrieves individual records by incident_id.

Both containers run as UID 10001. Compose connects them to an in-memory DynamoDB Local container. A separate smoke container initializes the local table and verifies the HTTP write/read path. Unit tests cover service behavior and failures; Moto verifies the SDK-backed cross-service path independently of Docker.

## Existing infrastructure code

Terraform defines networking, ECR, DynamoDB, EKS and IAM. Kubernetes defines two replicated API deployments with ClusterIP services and process health probes. These files are not evidence of a verified current rollout. Database permissions currently belong to worker nodes, images use latest tags, and the configured cluster version needs a support review before deployment.

## Planned capabilities

Workload-specific IAM, immutable releases, authenticated access, bounded list pagination, dependency readiness, deployment automation and centralized observability remain. There is no separate classifier process, dashboard or incident update API. Older generic learning notes describe exercises and possible practices, not implemented platform guarantees.
