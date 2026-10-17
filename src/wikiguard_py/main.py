"""FastAPI application entrypoint — rules CRUD + alert history (Stage 6),
dashboard (Stage 7)."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from wikiguard_py.api.alerts import router as alerts_router
from wikiguard_py.api.stats import router as stats_router
from wikiguard_py.api.threshold_rules import router as threshold_rules_router
from wikiguard_py.api.window_count_rules import router as window_count_rules_router
from wikiguard_py.persistence.database import create_tables
from wikiguard_py.redis_client import redis_client

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await redis_client.aclose()


app = FastAPI(title="wikiguard-py", lifespan=lifespan)

app.include_router(threshold_rules_router)
app.include_router(window_count_rules_router)
app.include_router(alerts_router)
app.include_router(stats_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "dashboard.html")
