FROM docker.artifacts.smit.sise/python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system --no-cache .

# --- Runtime stage ---
FROM docker.artifacts.smit.sise/python:3.12-slim

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --no-create-home appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uvicorn", "bookstore.main:app", "--host", "0.0.0.0", "--port", "8080", "--limit-max-request-size", "1048576"]
