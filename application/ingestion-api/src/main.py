from fastapi import FastAPI, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from typing import Literal, Optional
from datetime import datetime, timezone
from uuid import uuid4
import os
import boto3
from botocore.exceptions import ClientError

app = FastAPI(title="ingestion-api", version="1.0.0")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
INCIDENTS_TABLE = os.getenv("INCIDENTS_TABLE", "incident-response-incidents")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION, endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL"))
table = dynamodb.Table(INCIDENTS_TABLE)


PRIORITY_BY_SEVERITY = {
    "critical": "p1",
    "high": "p2",
    "medium": "p3",
    "low": "p4",
}


class AlertPayload(BaseModel):
    # Whitespace-only values are stripped first, so min_length rejects them.
    model_config = ConfigDict(str_strip_whitespace=True)

    source: str = Field(..., min_length=1, max_length=128, examples=["cloudwatch"])
    service_name: str = Field(..., min_length=1, max_length=128, examples=["payment-service"])
    # Unknown severities are rejected rather than silently assigned a priority.
    severity: Literal["critical", "high", "medium", "low"] = Field(..., examples=["high"])
    # Bounded well below the 400 KB DynamoDB item limit.
    message: str = Field(..., min_length=1, max_length=4096, examples=["CPU usage exceeded 90% for 5 minutes"])
    timestamp: Optional[AwareDatetime] = Field(default=None, examples=["2026-04-20T12:00:00Z"])

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingestion-api"}


@app.post("/alerts")
def ingest_alert(payload: AlertPayload):
    incident_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    timestamp = payload.timestamp.astimezone(timezone.utc).isoformat() if payload.timestamp else created_at

    record = {
        "incident_id": incident_id,
        "source": payload.source,
        "service_name": payload.service_name,
        "severity": payload.severity,
        "message": payload.message,
        "timestamp": timestamp,
        "status": "open",
        "priority": map_priority(payload.severity),
        "assigned_team": map_team(payload.service_name),
        "created_at": created_at,
    }

    try:
        table.put_item(Item=record)
    except ClientError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store incident: {exc.response['Error']['Message']}"
        ) from exc

    return {
        "message": "Alert ingested successfully",
        "incident_id": incident_id,
        "record": record,
    }


def map_priority(severity: str) -> str:
    return PRIORITY_BY_SEVERITY[severity.lower()]


def map_team(service_name: str) -> str:
    service_name = service_name.lower()

    if "payment" in service_name:
        return "finops"
    if "auth" in service_name:
        return "identity"
    if "network" in service_name:
        return "platform"
    return "sre"
