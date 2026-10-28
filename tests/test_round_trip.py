"""Both real API handlers against one isolated Moto DynamoDB table."""
import importlib.util
from pathlib import Path

import boto3
from fastapi.testclient import TestClient
from moto import mock_aws

ROOT = Path(__file__).resolve().parents[1]

def load_service(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "application" / name / "src" / "main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_alert_to_incident(monkeypatch):
    for key, value in {"AWS_ACCESS_KEY_ID": "testing", "AWS_SECRET_ACCESS_KEY": "testing", "AWS_SESSION_TOKEN": "testing", "AWS_REGION": "us-east-1", "AWS_EC2_METADATA_DISABLED": "true", "INCIDENTS_TABLE": "round-trip"}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("DYNAMODB_ENDPOINT_URL", raising=False)
    with mock_aws():
        boto3.resource("dynamodb", region_name="us-east-1").create_table(
            TableName="round-trip", KeySchema=[{"AttributeName": "incident_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "incident_id", "AttributeType": "S"}], BillingMode="PAY_PER_REQUEST")
        ingestion = TestClient(load_service("ingestion-api").app)
        incidents = TestClient(load_service("incident-api").app)
        payload = {"source": "integration", "service_name": "payment-api", "severity": "CRITICAL", "message": "Payment outage", "timestamp": "2026-09-14T12:00:00Z"}
        result = ingestion.post("/alerts", json=payload)
        assert result.status_code == 200
        record = result.json()["record"]
        assert record["priority"] == "p1"
        assert record["assigned_team"] == "finops"
        assert record["timestamp"] == "2026-09-14T12:00:00+00:00"
        fetched = incidents.get("/incidents/" + record["incident_id"])
        assert fetched.status_code == 200
        assert fetched.json() == record
        assert incidents.get("/incidents?status=open&severity=critical").json() == {"count": 1, "incidents": [record]}
        assert incidents.get("/incidents?severity=low").json() == {"count": 0, "incidents": []}
