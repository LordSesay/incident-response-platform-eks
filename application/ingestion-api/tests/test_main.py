import os
from unittest.mock import Mock

os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from fastapi.testclient import TestClient
from src import main

client = TestClient(main.app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ingestion-api",
    }


def test_ingest_alert(monkeypatch):
    mock_table = Mock()
    monkeypatch.setattr(main, "table", mock_table)

    payload = {
        "source": "cloudwatch",
        "service_name": "payment-service",
        "severity": "high",
        "message": "CPU usage exceeded threshold",
    }

    response = client.post("/alerts", json=payload)

    assert response.status_code == 200

    body = response.json()
    record = body["record"]

    assert body["message"] == "Alert ingested successfully"
    assert body["incident_id"] == record["incident_id"]
    assert record["source"] == "cloudwatch"
    assert record["service_name"] == "payment-service"
    assert record["severity"] == "high"
    assert record["priority"] == "p2"
    assert record["assigned_team"] == "finops"
    assert record["status"] == "open"
    assert record["incident_id"]
    assert record["created_at"]

    mock_table.put_item.assert_called_once_with(Item=record)
import pytest
from botocore.exceptions import ClientError

@pytest.mark.parametrize("severity,priority", [("CRITICAL", "p1"), ("high", "p2"), ("medium", "p3"), ("low", "p4"), ("unknown", "p4")])
def test_priority_mapping(severity, priority):
    assert main.map_priority(severity) == priority

@pytest.mark.parametrize("service,team", [("PAYMENT", "finops"), ("auth-api", "identity"), ("network", "platform"), ("other", "sre")])
def test_team_mapping(service, team):
    assert main.map_team(service) == team

def test_invalid_payload_does_not_write(monkeypatch):
    table = Mock()
    monkeypatch.setattr(main, "table", table)
    assert client.post("/alerts", json={"severity": "high"}).status_code == 422
    table.put_item.assert_not_called()

def test_write_failure(monkeypatch):
    table = Mock()
    table.put_item.side_effect = ClientError({"Error": {"Code": "InternalServerError", "Message": "Unavailable"}}, "PutItem")
    monkeypatch.setattr(main, "table", table)
    response = client.post("/alerts", json={"source": "test", "service_name": "auth", "severity": "high", "message": "test"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to store incident: Unavailable"}
