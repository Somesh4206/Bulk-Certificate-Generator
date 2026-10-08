"""Tests: Pydantic validation (422s, no job created on bad input)."""


def test_invalid_recipient_data(client):
    # invalid email
    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "Certificate of Participation",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [{"name": "Bad User", "email": "not-an-email"}],
        },
    )
    assert r.status_code == 422

    # empty name
    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "Certificate of Participation",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [{"name": "", "email": "ok@example.com"}],
        },
    )
    assert r.status_code == 422

    # empty title
    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [{"name": "Somesh", "email": "s@example.com"}],
        },
    )
    assert r.status_code == 422


def test_empty_recipient_list(client):
    r = client.post(
        "/api/jobs",
        json={
            "certificate_title": "Certificate of Participation",
            "event_name": "Aereo Cloud Workshop",
            "date": "2026-10-08",
            "recipients": [],
        },
    )
    assert r.status_code == 422
