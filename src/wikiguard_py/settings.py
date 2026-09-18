"""Centralized configuration.

Defaults match what every module hardcoded so far (localhost + the
host-mapped Docker ports) — nothing changes for a normal local run. Values
become overridable via environment variables, needed once a service runs
*inside* a container (Stage 8): there, "localhost:9094" reaches nothing —
the right address is the service name on its internal port (kafka:9092).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9094"
    redis_host: str = "localhost"
    redis_port: int = 6380
    database_url: str = "postgresql+asyncpg://wikiguard:wikiguard@localhost:5433/wikiguard"


settings = Settings()
