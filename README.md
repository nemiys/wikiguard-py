# wikiguard-py

Real-time Wikipedia edit-integrity monitor — a Python/FastAPI/Kafka port of
[wiki-guard](../wiki-guard) (Java/Spring Boot), built from first principles
around Kafka as a high-scale streaming pipeline rather than ported line by
line. See `docs/adr/` for the architecture decision log.

Status: Stage 0 (scaffolding) in progress.

## Local development

```bash
uv sync
docker compose up -d        # Postgres :5433, Redis :6380, Kafka :9094
uv run uvicorn wikiguard_py.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`
