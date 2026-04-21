from fastapi import FastAPI, HTTPException
from typing import Optional
import os
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

app = FastAPI(title="incident-api", version="1.0.0")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
INCIDENTS_TABLE = os.getenv("INCIDENTS_TABLE", "incident-response-incidents")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(INCIDENTS_TABLE)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "incident-api"}


@app.get("/incidents")
def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None
):
    try:
        response = table.scan()
        items = response.get("Items", [])

        if status:
            items = [item for item in items if item.get("status") == status]
        if severity:
            items = [item for item in items if item.get("severity") == severity.lower()]

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