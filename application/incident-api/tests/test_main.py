import os
from unittest.mock import Mock, call

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
        "service": "incident-api",
    }


def test_list_incidents(monkeypatch):
    mock_table = Mock()
    mock_table.scan.return_value = {
        "Items": [
            {
                "incident_id": "inc-123",
                "severity": "high",
                "status": "open",
            }
        ]
    }
    monkeypatch.setattr(main, "table", mock_table)

    response = client.get("/incidents")

    assert response.status_code == 200
    assert response.json() == {
        "count": 1,
        "incidents": [
            {
                "incident_id": "inc-123",
                "severity": "high",
                "status": "open",
            }
        ],
    }
    mock_table.scan.assert_called_once_with()


def test_get_incident(monkeypatch):
    mock_table = Mock()
    incident = {
        "incident_id": "inc-123",
        "severity": "high",
        "status": "open",
    }
    mock_table.get_item.return_value = {"Item": incident}
    monkeypatch.setattr(main, "table", mock_table)

    response = client.get("/incidents/inc-123")

    assert response.status_code == 200
    assert response.json() == incident
    mock_table.get_item.assert_called_once_with(
        Key={"incident_id": "inc-123"}
    )


def test_get_incident_returns_404(monkeypatch):
    mock_table = Mock()
    mock_table.get_item.return_value = {}
    monkeypatch.setattr(main, "table", mock_table)

    response = client.get("/incidents/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Incident not found"}
import pytest
from botocore.exceptions import ClientError

def test_filtered_scan_includes_later_pages(monkeypatch):
    table = Mock()
    key = {"incident_id": "first"}
    expected = {"incident_id": "second", "severity": "high", "status": "open"}
    table.scan.side_effect = [
        {"Items": [{"incident_id": "first", "severity": "low", "status": "open"}], "LastEvaluatedKey": key},
        {"Items": [expected, {"incident_id": "third", "severity": "high", "status": "closed"}]},
    ]
    monkeypatch.setattr(main, "table", table)
    response = client.get("/incidents?status=open&severity=HIGH")
    assert response.status_code == 200
    assert response.json() == {"count": 1, "incidents": [expected]}
    assert table.scan.call_args_list == [call(), call(ExclusiveStartKey=key)]

def test_empty_list(monkeypatch):
    table = Mock()
    table.scan.return_value = {}
    monkeypatch.setattr(main, "table", table)
    assert client.get("/incidents").json() == {"count": 0, "incidents": []}

@pytest.mark.parametrize("path,operation", [("/incidents", "scan"), ("/incidents/example", "get_item")])
def test_read_failure(monkeypatch, path, operation):
    table = Mock()
    getattr(table, operation).side_effect = ClientError({"Error": {"Code": "InternalServerError", "Message": "Unavailable"}}, operation)
    monkeypatch.setattr(main, "table", table)
    assert client.get(path).status_code == 500

from botocore.exceptions import EndpointConnectionError

def test_liveness_alias():
    assert client.get("/health/live").json() == {"status": "ok", "service": "incident-api"}

@pytest.mark.parametrize("table_status", ["ACTIVE", "UPDATING"])
def test_ready_when_table_usable(monkeypatch, table_status):
    db = Mock()
    db.describe_table.return_value = {"Table": {"TableStatus": table_status}}
    monkeypatch.setattr(main, "readiness_client", db)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "incident-api"}
    db.describe_table.assert_called_once_with(TableName=main.INCIDENTS_TABLE)

@pytest.mark.parametrize("outcome", [
    ClientError({"Error": {"Code": "AccessDeniedException", "Message": "secret detail"}}, "DescribeTable"),
    EndpointConnectionError(endpoint_url="http://dynamodb.invalid"),
    {"Table": {"TableStatus": "CREATING"}},
])
def test_not_ready_returns_503_without_detail(monkeypatch, outcome):
    db = Mock()
    if isinstance(outcome, Exception):
        db.describe_table.side_effect = outcome
    else:
        db.describe_table.return_value = outcome
    monkeypatch.setattr(main, "readiness_client", db)
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "service": "incident-api"}
