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
| GitHub-hosted workflow | Passed on 2026-10-28; see hosted run below |
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

## Hosted CI run

[Run #2](https://github.com/LordSesay/incident-response-platform-eks/actions/runs/40741086253) passed on 2026-10-28 for commit `ea53089` (PR #1), on `ubuntu-latest` with Python 3.11.17. This commit adds stricter alert validation, so the test counts differ from the local record above. Commit authorship was later rewritten without changing content: the tested tree is `30f741c` on `main`, and `ea53089` remains visible in PR #1.

| Job / step | Result from the job log |
| --- | --- |
| Ingestion unit tests | 23 passed |
| Incident unit tests | 8 passed |
| Moto DynamoDB integration | 1 passed |
| `docker compose up --build --wait` (both images, health checks) | Passed |
| Compose smoke test | `PASS: both container health checks and alert -> DynamoDB -> incident read` |

This is a Compose run on a GitHub runner. It does not exercise the Kubernetes security context, Pod Security admission, AWS IAM, ECR or EKS.

## Next evidence to collect

1. ~~Push the reviewed changes and retain a passing GitHub Actions run link.~~ Done; see hosted CI run.
2. Review existing Terraform and Kubernetes configuration, including cluster version support, public network defaults, node IAM and mutable image references.
3. Publish immutable images, deploy a reviewed configuration, and capture rollout status plus an authenticated alert/read test in EKS.
4. Document workload IAM, observability, recovery and resource cleanup before claiming those capabilities.

Existing uncommitted Terraform, Kubernetes and build-log work was preserved. The generic historical build log and screenshot are not substituted for validation of the current release.
