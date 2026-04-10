#!/bin/bash
# Generate SQLAlchemy 2.0 models from database schema
# Equivalent to Spring Boot's jOOQ code generator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

OUTPUT_DIR="$PROJECT_ROOT/src/generated/db"

# Default to local dev database; override with DATASOURCE_URL env var
# Note: sqlacodegen needs a synchronous URL (postgresql://, not postgresql+asyncpg://)
DB_URL="${DATASOURCE_URL:-postgresql://bookstore:bookstore@localhost:5432/bookstore}"
# Strip async driver prefix if present
DB_URL="${DB_URL//+asyncpg/}"

echo "Generating SQLAlchemy models from database schema..."
echo "  Database: ${DB_URL%%@*}@***"
echo "  Output:   $OUTPUT_DIR/models.py"

sqlacodegen \
  --generator declarative \
  --outfile "$OUTPUT_DIR/models.py" \
  "$DB_URL"

echo "DB models generated successfully."
