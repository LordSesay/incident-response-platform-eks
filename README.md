# Incident Response Platform (EKS)

Two FastAPI services normalize incoming alerts, persist incidents in DynamoDB, and expose incident retrieval. This portfolio project is being developed toward deployment on Amazon EKS. Classification currently runs inside ingestion-api.

## Evidence and status

| Capability | Status |
| --- | --- |
| Alert ingestion, priority/team mapping, DynamoDB writes | Implemented |
| Incident listing, status/severity filters, lookup by ID | Implemented; listing follows DynamoDB scan pages |
| Deterministic unit tests and cross-service DynamoDB integration test | Implemented; see validation record below |
| Non-root Docker images and local Compose environment | Implemented; see validation record below |
| GitHub Actions unit, integration, and container checks | Workflow added; hosted run pending |
| Terraform VPC, ECR, DynamoDB, IAM, EKS and node group | Existing local implementation; deployment not verified in this work |
| Kubernetes deployments, ClusterIP services and health probes | Existing definitions; deployment not verified in this work |
| ECR publishing and automated EKS deployment | Pending |
| Separate classifier, dashboard, authentication, centralized metrics/logs | Pending |

A historical node screenshot exists in `docs/screenshots/`. It does not establish that these API images or the current infrastructure revision have been deployed successfully.

## Current application flow

```text
POST /alerts -> ingestion-api (classification) -> DynamoDB
                                                  |
GET /incidents or /incidents/{id} <- incident-api <-+
```

- Both services expose `GET /health` and FastAPI `/docs`.
- `POST /alerts` requires source, service_name, severity and message; timestamp is optional.
- Invalid payloads return `422` and are not stored: blank or oversized strings (source/service_name max 128, message max 4096), unknown severities, and timestamps that are not ISO 8601 with a UTC offset. Senders should treat `422` as a contract error, not retry it.
- Severity (case-insensitive) maps critical/high/medium/low to p1/p2/p3/p4. Timestamps are stored normalized to UTC.
- Service names containing payment/auth/network map to finops/identity/platform; others map to sre.
- Incidents start with status `open`. No incident update endpoint exists yet.

## Run the tests

Python 3.11 or 3.12:

```bash
python -m venv .venv
# Activate: Windows PowerShell .\.venv\Scripts\Activate.ps1
# Activate: macOS/Linux source .venv/bin/activate
python -m pip install -r requirements-test.txt
(cd application/ingestion-api && python -m pytest tests -q)
(cd application/incident-api && python -m pytest tests -q)
python -m pytest tests -q
```

On PowerShell, run each service test after `Push-Location application/ingestion-api` (or `incident-api`), then `Pop-Location`. Service tests run separately because both services use the module name `src.main`. Unit tests mock DynamoDB operations. The root integration test runs both APIs against one isolated Moto table, with test credentials and no AWS deployment.

## Run and verify the containers

With Docker Desktop (Linux containers) or Docker Engine and Compose:

```bash
docker compose up --build --wait ingestion-api incident-api
docker compose --profile test run --rm smoke
```

The smoke test initializes the disposable DynamoDB Local table, posts an alert through the ingestion container, retrieves it through the incident container, and checks classification and filtering. Run it before using the APIs manually.

- Ingestion: http://localhost:8001/docs
- Incidents: http://localhost:8002/docs

```bash
docker compose --profile test down --volumes --remove-orphans
```

Only loopback API ports are published. DynamoDB data is in memory and is discarded when its container stops. Compose supplies local dummy credentials; AWS credentials are not required.

## Configuration

| Variable | Default / purpose |
| --- | --- |
| AWS_REGION | us-east-1 |
| INCIDENTS_TABLE | incident-response-incidents |
| DYNAMODB_ENDPOINT_URL | Unset for AWS; Compose sets the local emulator endpoint |

`/health` reports process health, not database readiness. The APIs currently lack authentication, use full-table scans for listing, and return AWS error details. These are development services; authentication, bounded pagination and error sanitization remain before external exposure.

## Infrastructure boundary

The existing Terraform configuration creates public subnets, ECR repositories, a DynamoDB table, an EKS cluster and managed nodes. It currently grants database access through the node role. The Kubernetes manifests use account-specific ECR URLs and mutable `latest` tags. Terraform configuration and a screenshot are evidence of implementation/history, not proof of a current successful application deployment.

Next milestone: review infrastructure defaults, replace node-level database access with workload-specific IAM, publish immutable image tags, verify a rollout and alert round trip in EKS, and record deployment and cleanup evidence. The legacy setup/cleanup scripts and older learning notes require review before use.

## Terraform state

State is stored in S3 with native lock files (Terraform 1.10+). The bucket is created once, outside this configuration, so the state does not depend on the resources it describes:

```bash
BUCKET=<globally-unique-name>
aws s3api create-bucket --bucket "$BUCKET" --region us-east-1   # other regions also need --create-bucket-configuration LocationConstraint=<region>
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
cp infrastructure/backend.hcl.example infrastructure/backend.hcl   # then set bucket
terraform -chdir=infrastructure init -backend-config=backend.hcl
```

Existing local state is moved with `terraform init -migrate-state -backend-config=backend.hcl`. `.terraform.lock.hcl` is committed and pins the AWS provider build for Linux, Windows and macOS. The cluster uses the STANDARD upgrade policy, so it is upgraded automatically at the end of standard support instead of entering paid extended support.

## Validation record

See [baseline validation](docs/baseline-validation.md) for commands, results and remaining deployment checks. The CI workflow runs tests before building and smoke-testing containers; it does not publish images or deploy AWS resources.
