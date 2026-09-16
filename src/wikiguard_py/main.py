"""FastAPI application entrypoint.

Stage 0 skeleton — just enough to prove the app boots and the toolchain
(uv, FastAPI, uvicorn) works end-to-end. The REST API surface (rules CRUD,
alerts) is built in Stage 6, once the domain/producer/consumer/persistence
layers underneath it exist.
"""

from fastapi import FastAPI

app = FastAPI(title="wikiguard-py")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
