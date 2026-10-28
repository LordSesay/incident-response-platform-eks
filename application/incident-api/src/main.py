from fastapi import FastAPI, HTTPException
from typing import Optional
import logging
import os
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="incident-api", version="1.0.0")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
INCIDENTS_TABLE = os.getenv("INCIDENTS_TABLE", "incident-response-incidents")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION, endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL"))
table = dynamodb.Table(INCIDENTS_TABLE)

# Readiness uses its own client with short timeouts and no retries, so a probe
# fails fast instead of holding a request thread while DynamoDB is unreachable.
readiness_client = boto3.client(
    "dynamodb",
    region_name=AWS_REGION,
    endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL"),
    config=Config(connect_timeout=1, read_timeout=1, retries={"total_max_attempts": 1}),
)


# /health is kept as an alias of /health/live for Compose and existing callers.
@app.get("/health")
@app.get("/health/live")
def health_check():
    return {"status": "ok", "service": "incident-api"}


@app.get("/health/ready")
def readiness_check():
    # Reports whether this instance can reach its table. Error details go to the
    # log, not the response.
    try:
        table_status = readiness_client.describe_table(TableName=INCIDENTS_TABLE)["Table"]["TableStatus"]
    except (BotoCoreError, ClientError) as exc:
        logger.warning("Readiness check failed: %s", exc)
        table_status = None

    if table_status not in ("ACTIVE", "UPDATING"):
        return JSONResponse(status_code=503, content={"status": "unavailable", "service": "incident-api"})
    return {"status": "ok", "service": "incident-api"}


@app.get("/incidents")
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None
):
    try:
        response = table.scan()
        items = response.get("Items", [])
        while response.get("LastEvaluatedKey"):
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))

        # Stored values are lowercase, so filters are case-insensitive.
        if status:
            items = [item for item in items if item.get("status") == status.strip().lower()]
        if severity:
            items = [item for item in items if item.get("severity") == severity.strip().lower()]

        return {"count": len(items), "incidents": items}
    except ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve incidents: {exc.response['Error']['Message']}"
        ) from exc


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    try:
        response = table.get_item(Key={"incident_id": incident_id})
        item = response.get("Item")

        if not item:
            raise HTTPException(status_code=404, detail="Incident not found")

        return item
    except ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve incident: {exc.response['Error']['Message']}"
        ) from exc
