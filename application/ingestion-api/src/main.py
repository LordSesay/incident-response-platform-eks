from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
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


class AlertPayload(BaseModel):
    source: str = Field(..., example="cloudwatch")
    service_name: str = Field(..., example="payment-service")
    severity: str = Field(..., example="high")
    message: str = Field(..., example="CPU usage exceeded 90% for 5 minutes")
    timestamp: Optional[str] = Field(
        default=None,
        example="2026-04-20T12:00:00Z"
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ingestion-api"}


@app.post("/alerts")
def ingest_alert(payload: AlertPayload):
    incident_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    record = {
        "incident_id": incident_id,
        "source": payload.source,
        "service_name": payload.service_name,
        "severity": payload.severity.lower(),
        "message": payload.message,
        "timestamp": payload.timestamp or created_at,
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
    severity = severity.lower()
    mapping = {
        "critical": "p1",
        "high": "p2",
        "medium": "p3",
        "low": "p4",
    }
    return mapping.get(severity, "p4")


def map_team(service_name: str) -> str:
    service_name = service_name.lower()

    if "payment" in service_name:
        return "finops"
    if "auth" in service_name:
        return "identity"
    if "network" in service_name:
        return "platform"
    return "sre"
