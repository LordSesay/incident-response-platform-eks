# Application and container baseline validation

Validated locally on 2026-09-14 using Windows, Python 3.12.4 and Docker Desktop with Linux containers. Container runtime: Python 3.11. No AWS credentials or deployed resources were used for these checks.

| Check | Result |
| --- | --- |
| Ingestion unit tests | 13 passed |
| Incident unit tests | 8 passed |
| Moto DynamoDB integration | 1 passed |
| Both Docker image builds | Passed |
| Both container health checks | Passed |
| HTTP alert write -> DynamoDB Local -> incident read/filter | Passed |
| GitHub-hosted workflow | Pending push and hosted run |
| ECR/EKS release | Not attempted |

Unit tests were executed in each service directory with `python -m pytest tests -q -p no:cacheprovider`; the integration test used the same command at the repository root. Tests cover classification rules, required fields, successful persistence, missing incidents, storage failures, empty results, filtering across scan pages and a complete SDK-backed round trip. Dependency deprecation warnings remain in the existing FastAPI/Pydantic/botocore stack; they did not fail the tests.

Container commands:

```bash
docker compose up --build --wait ingestion-api incident-api
docker compose --profile test run --rm smoke
```

Observed smoke output:

```text
PASS: both container health checks and alert -> DynamoDB -> incident read
```

The smoke script initializes only the Compose emulator table and verifies actual HTTP requests across separate application containers. This proves the local application/container baseline, not AWS IAM, network access, ECR publishing or EKS deployment.

## Next evidence to collect

1. Push the reviewed changes and retain a passing GitHub Actions run link.
2. Review existing Terraform and Kubernetes configuration, including cluster version support, public network defaults, node IAM and mutable image references.
3. Publish immutable images, deploy a reviewed configuration, and capture rollout status plus an authenticated alert/read test in EKS.
4. Document workload IAM, observability, recovery and resource cleanup before claiming those capabilities.

Existing uncommitted Terraform, Kubernetes and build-log work was preserved. The generic historical build log and screenshot are not substituted for validation of the current release.
