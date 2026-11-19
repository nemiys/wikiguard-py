FROM python:3.12-slim

# Pinned, like every other dependency: `latest` could change the build without any change here.
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY src ./src
RUN uv sync --frozen

CMD ["uv", "run", "python", "-m", "wikiguard_py.consumer.main"]
