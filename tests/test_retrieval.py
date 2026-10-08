"""Tests: retrieving generated PDFs."""
from tests.conftest import wait_for_completion


def test_retrieve_certificate(client):
    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "Certificate of Participation",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [{"name": "Somesh M", "email": "somesh@example.com"}],
        },
    )
    assert r.status_code == 202
    job = wait_for_completion(client, r.json()["job_id"])
    assert job["status"] == "completed"
    cert_id = job["certificates"][0]["id"]

    dl = client.get(f"/api/certificates/{cert_id}")
    assert dl.status_code == 200, dl.text[:200] if hasattr(dl, "text") else ""
    assert "application/pdf" in dl.headers["content-type"]
    assert dl.content[:4] == b"%PDF"


def test_certificate_not_found(client):
    r = client.get("/api/certificates/999999")
    assert r.status_code == 404
