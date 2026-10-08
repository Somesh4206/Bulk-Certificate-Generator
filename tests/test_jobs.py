"""Tests: creating jobs + job status/progress + 404."""
from tests.conftest import wait_for_completion


def _payload(**over):
    data = {
        "certificate_title": "Certificate of Participation",
        "event_name": "Aereo Cloud Workshop",
        "date": "2026-10-08",
        "recipients": [
            {"name": "Somesh M", "email": "somesh@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"},
        ],
    }
    data.update(over)
    return data


def test_create_generation_job(client):
    r = client.post("/api/jobs", json=_payload())
    assert r.status_code == 202, r.text
    body = r.json()
    assert "job_id" in body
    assert body["status"] == "queued"
    assert body["total"] == 2


def test_job_status(client):
    r = client.post("/api/jobs", json=_payload())
    job_id = r.json()["job_id"]
    job = wait_for_completion(client, job_id)
    assert job["job_id"] == job_id
    assert job["total"] == 2
    assert job["status"] in (
        "queued",
        "processing",
        "completed",
        "completed_with_errors",
    )
    assert len(job["certificates"]) == 2
    # happy path: both succeed
    assert job["successful"] + job["failed"] == 2


def test_job_not_found(client):
    r = client.get("/api/jobs/does-not-exist")
    assert r.status_code == 404
