FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

# deps layer — cached until pyproject.toml or uv.lock changes
# --no-install-project installs all dependencies but skips building the project
# package itself, which needs src/ to exist. This keeps the heavy download step
# cached even when your source code changes.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# source — rebuilds on code changes, but the deps layer above is reused from cache
COPY src/ ./src/

# now install the project package itself (fast — all deps are already cached above)
RUN uv sync --frozen --no-dev

ENV PYTHONPATH=src

EXPOSE 8000

# default command is the API; scheduler overrides this in docker-compose.yml
CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
