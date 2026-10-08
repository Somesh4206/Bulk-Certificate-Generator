"""FastAPI entrypoint."""
from fastapi import FastAPI

from app.database import Base, engine
from app.models import Certificate, GenerationJob  # noqa: F401 (register tables)
from app.routes import jobs

app = FastAPI(title="Bulk Certificate Generator")

Base.metadata.create_all(bind=engine)

app.include_router(jobs.router, prefix="/api")


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}
