#!/bin/bash
# Generate Pydantic v2 models from OpenAPI spec (Contract-First)
# Equivalent to Spring Boot's openapi-generator with delegatePattern
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

INPUT_SPEC="$PROJECT_ROOT/src/resources/swagger/openapi.yml"
OUTPUT_DIR="$PROJECT_ROOT/src/generated/openapi"

echo "Generating Pydantic models from OpenAPI spec..."
echo "  Input:  $INPUT_SPEC"
echo "  Output: $OUTPUT_DIR/models.py"

datamodel-codegen \
  --input "$INPUT_SPEC" \
  --input-file-type openapi \
  --output-model-type pydantic_v2.BaseModel \
  --use-field-description \
  --field-constraints \
  --use-default \
  --snake-case-field \
  --target-python-version 3.12 \
  --output "$OUTPUT_DIR/models.py"

echo "Models generated successfully."
