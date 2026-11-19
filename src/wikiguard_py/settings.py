"""Centralized configuration.

Defaults target a local run (localhost + the host-mapped Docker ports).
Every value is overridable via environment variables, which is needed when
a service runs *inside* a container: there, "localhost:9094" reaches nothing —
the right address is the service name on its internal port (kafka:9092).
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9094"
    redis_host: str = "localhost"
    redis_port: int = 6380
    database_url: str = "postgresql+asyncpg://wikiguard:wikiguard@localhost:5433/wikiguard"


settings = Settings()
