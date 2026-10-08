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


def test_individual_certificate_failure(client, monkeypatch):
    """One bad certificate must not stop the rest (failure via mock)."""
    import app.services.job_service as job_service

    real_render = job_service.render_certificate

    def flaky_render(path, recipient_name, *args, **kwargs):
        if recipient_name == "Bad User":
            raise ValueError("Simulated generation failure for testing")
        return real_render(path, recipient_name, *args, **kwargs)

    monkeypatch.setattr(job_service, "render_certificate", flaky_render)

    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "Certificate of Participation",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [
                {"name": "Good User", "email": "good@example.com"},
                {"name": "Bad User", "email": "bad@example.com"},
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
    assert by_name["Bad User"]["status"] == "failed"
    assert by_name["Bad User"]["error"]
