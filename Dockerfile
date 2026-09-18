FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY src ./src
RUN uv sync --frozen

CMD ["uv", "run", "python", "-m", "wikiguard_py.consumer.main"]
