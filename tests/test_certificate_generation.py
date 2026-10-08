"""Tests: PDF generation + per-certificate failure isolation."""
from templates.certificate_template import generate_certificate_pdf
from tests.conftest import wait_for_completion


def test_certificate_generation(tmp_path):
    out = tmp_path / "cert.pdf"
    generate_certificate_pdf(
        str(out), "Somesh M", "Certificate of Participation",
        "Aereo Cloud Workshop", "08 October 2026",
    )
    assert out.exists()
    assert out.stat().st_size > 1000
    with open(out, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_individual_certificate_failure(client):
    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "Certificate of Participation",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [
                {"name": "Good User", "email": "good@example.com"},
                {"name": "FAIL_Broken User", "email": "bad@example.com"},
            ],
        },
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    job = wait_for_completion(client, job_id)
    # One failure must NOT stop the other certificate.
    assert job["status"] == "completed_with_errors"
    assert job["successful"] == 1
    assert job["failed"] == 1
    by_name = {c["recipient_name"]: c for c in job["certificates"]}
    assert by_name["Good User"]["status"] == "success"
    assert by_name["FAIL_Broken User"]["status"] == "failed"
    assert by_name["FAIL_Broken User"]["error"]
