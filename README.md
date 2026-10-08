# Bulk Certificate Generator

Backend API that accepts **one bulk request with many recipients** and generates **one PDF certificate per recipient** using a single predefined template. Built as an SDE Intern assignment for Aereo Cloud.

## Overview

Client sends `POST /api/jobs` with certificate details + a list of recipients. The API validates the data, creates a job row plus one certificate row per recipient, returns a `job_id` immediately, and generates PDFs in the background. The client polls `GET /api/jobs/{job_id}` for progress and downloads PDFs via `GET /api/certificates/{certificate_id}`.

One bad recipient never stops the rest: each certificate is processed inside its own `try/except`, marked `success`/`failed` individually, and the job finishes as `completed` or `completed_with_errors`.

## Features

- Bulk creation: one request → many certificates
- Pydantic validation (title, event, date, non-empty recipients, name, valid email)
- Job tracking: `queued → processing → completed / completed_with_errors / failed`
- Per-certificate tracking: `pending → processing → success / failed`
- Failure isolation with stored `error_message`
- PDF generation with ReportLab (one predefined template)
- File retrieval by certificate ID (no path exposure, no traversal)
- Tests with isolated temp DB + temp cert directory
- Swagger docs via FastAPI

## Tech Stack

- Python 3.11+ (also works on 3.10)
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic (EmailStr)
- ReportLab
- Pytest + FastAPI TestClient
- Uvicorn

## Project Structure

```
bulk-certificate-generator/
├── app/
│   ├── main.py                    # FastAPI app, router, table creation
│   ├── database.py                # SQLite engine, SessionLocal, get_db
│   ├── models/job.py              # generation_jobs table
│   ├── models/certificate.py      # certificates table
│   ├── schemas/job.py             # request/response validation
│   ├── routes/jobs.py             # POST /api/jobs, GET job, GET certificate
│   └── services/
│       ├── job_service.py         # BackgroundTasks worker (per-cert try/except)
│       └── certificate_generator.py # safe paths + template call
├── templates/certificate_template.py # the ONE ReportLab design
├── generated_certificates/        # output: <job_id>/certificate_<id>.pdf
├── tests/                         # jobs, validation, generation, retrieval
├── requirements.txt
├── README.md
└── certificate.db                 # created on first run (gitignored)
```

## Setup

Requires Python 3.11+.

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

## Run Application

```bash
uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

Health: `GET /health` → `{"status": "ok"}`

## API Documentation

### POST /api/jobs — create bulk job (202 Accepted)

```json
{
  "certificate_title": "Certificate of Participation",
  "event_name": "Aereo Cloud Workshop",
  "date": "2026-10-08",
  "recipients": [
    {"name": "Somesh M", "email": "somesh@example.com"},
    {"name": "Rahul Kumar", "email": "rahul@example.com"}
  ]
}
```

Response:

```json
{
  "job_id": "abc123...",
  "status": "queued",
  "total": 2
}
```

Validation errors return `422` (bad email, empty name/title, empty recipient list, bad date).

### GET /api/jobs/{job_id} — job status and progress

```json
{
  "job_id": "abc123",
  "status": "completed_with_errors",
  "total": 4,
  "successful": 3,
  "failed": 1,
  "certificates": [
    {"id": 1, "recipient_name": "Somesh M", "status": "success", "error": null},
    {"id": 3, "recipient_name": "Invalid User", "status": "failed", "error": "..."}
  ]
}
```

`404` if job not found.

### GET /api/certificates/{certificate_id} — download PDF

- Success → `200 application/pdf` with filename `certificate_<id>.pdf`
- Unknown ID → `404`
- Exists but failed/pending → `422` with status reason
- Never exposes filesystem paths; path is built server-side from integer PKs only.

## Checking Job Status

```bash
curl http://127.0.0.1:8000/api/jobs/<job_id>
```

## Retrieving Certificate

```bash
curl -O http://127.0.0.1:8000/api/certificates/1
```

## Running Tests

```bash
pytest -v
```

Tests use a temporary SQLite file and temporary cert directory per test (see `tests/conftest.py`), so the real `certificate.db` and `generated_certificates/` are never touched. A name starting with `FAIL_` forces a per-certificate failure to prove isolation.

## Design Decisions

- **Why FastAPI:** built-in validation, BackgroundTasks, and Swagger with minimal code — ideal for an assignment-sized API.
- **Why SQLite:** zero setup, file-local, sufficient for demo scale; easy to swap for Postgres later via SQLAlchemy URL.
- **Why SQLAlchemy:** clean ORM models + relationships (`GenerationJob.certificates`), no raw SQL.
- **Why BackgroundTasks:** bulk PDF generation takes time; the client should get a `job_id` immediately and poll. `BackgroundTasks` runs the worker in-process with no extra infra. It is **not** a distributed queue — a production system would move `process_job` to Celery/RQ + Redis with retries and separate workers. This is documented honestly, not oversold.
- **Why one predefined template:** the assignment forbids template editors/uploads; one ReportLab layout keeps the scope explainable.
- **Why individual failure handling:** bulk means partial success is normal. Each certificate gets its own `try/except`; errors are stored on the row and the loop continues.

Flow:

```
POST /api/jobs → validate → insert job + pending certs → 202 + job_id
BackgroundTasks → job=processing → for each cert: try render PDF → success
                  / except → failed + error_message → continue
               → counts → completed / completed_with_errors
```

## Error Handling

- Request errors → FastAPI/Pydantic `422`, malformed JSON handled by FastAPI.
- `GET` unknown job/cert → `404`.
- Per-certificate exception → `cert.status=failed`, `error_message` saved (truncated), `file_path=None`, loop continues. No stack traces leak to clients; full trace goes to server logs.
- Whole-job crash (e.g. DB down) → `job.status=failed`.
- File serving validates DB status first, then checks the file exists.

## Limitations

- Local file storage (`generated_certificates/`), no object store.
- SQLite single-writer limits; no pagination on huge jobs (all certs returned in status).
- `BackgroundTasks` is in-process: jobs are lost on restart, no retries, no horizontal scale.
- Single certificate template only.
- No auth (out of scope per assignment).

## Certificate Database

`certificate.db` is created automatically in the project root on first app start (`Base.metadata.create_all`). It is gitignored.
