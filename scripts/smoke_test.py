"""Run inside the Compose test profile; uses only the disposable local table."""
import json
import os
import time
import urllib.request
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

endpoint = os.environ["DYNAMODB_ENDPOINT_URL"]
if endpoint != "http://dynamodb:8000":
    raise RuntimeError("This smoke test must target the Compose DynamoDB emulator")
db = boto3.client("dynamodb", region_name="us-east-1", endpoint_url=endpoint)
for attempt in range(30):
    try:
        db.create_table(TableName=os.environ["INCIDENTS_TABLE"], KeySchema=[{"AttributeName": "incident_id", "KeyType": "HASH"}], AttributeDefinitions=[{"AttributeName": "incident_id", "AttributeType": "S"}], BillingMode="PAY_PER_REQUEST")
        break
    except db.exceptions.ResourceInUseException:
        break
    except (EndpointConnectionError, ClientError):
        if attempt == 29:
            raise
        time.sleep(1)

def request(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        assert response.status == 200
        return json.load(response)

assert request("http://ingestion-api:8000/health")["status"] == "ok"
assert request("http://incident-api:8000/health")["status"] == "ok"
result = request("http://ingestion-api:8000/alerts", {"source": "smoke-test", "service_name": "payment-api", "severity": "CRITICAL", "message": "Container round trip"})
record = result["record"]
assert record["priority"] == "p1" and record["assigned_team"] == "finops"
assert request("http://incident-api:8000/incidents/" + record["incident_id"]) == record
assert record in request("http://incident-api:8000/incidents?status=open&severity=critical")["incidents"]
print("PASS: both container health checks and alert -> DynamoDB -> incident read")
