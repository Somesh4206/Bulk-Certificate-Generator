"""Isolated test setup: temp SQLite DB + temp certificate directory."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
import app.services.job_service as job_service


@pytest.fixture()
def client(tmp_path, monkeypatch):
    cert_dir = tmp_path / "certs"
    cert_dir.mkdir()
    monkeypatch.setenv("CERT_OUTPUT_DIR", str(cert_dir))

    db_file = tmp_path / "test.db"
    test_engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    TestingSession = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    old_session_local = job_service.SessionLocal
    job_service.SessionLocal = TestingSession

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    job_service.SessionLocal = old_session_local
    test_engine.dispose()


def wait_for_completion(client: TestClient, job_id: str, timeout: float = 10.0):
    """Poll job status until terminal state (BackgroundTasks may lag)."""
    import time

    terminal = {"completed", "completed_with_errors", "failed"}
    start = time.time()
    last = None
    while time.time() - start < timeout:
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200
        last = r.json()
        if last["status"] in terminal:
            return last
        time.sleep(0.2)
    return last
