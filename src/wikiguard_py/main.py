"""FastAPI application entrypoint — rules CRUD + alert history (Stage 6)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from wikiguard_py.api.alerts import router as alerts_router
from wikiguard_py.api.threshold_rules import router as threshold_rules_router
from wikiguard_py.api.window_count_rules import router as window_count_rules_router
from wikiguard_py.persistence.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="wikiguard-py", lifespan=lifespan)

app.include_router(threshold_rules_router)
app.include_router(window_count_rules_router)
app.include_router(alerts_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
