#!/bin/bash
# Validate that the running FastAPI app's OpenAPI schema matches the source spec.
# Compares operation IDs, paths, and schema names to detect contract drift.
set -euo pipefail

SPEC_FILE="${1:-src/resources/swagger/openapi.yml}"
APP_URL="${2:-http://localhost:8080}"

echo "Validating API contract..."
echo "  Spec:    $SPEC_FILE"
echo "  App:     $APP_URL/api/openapi.json"

python3 << PYEOF
import json
import sys

import yaml

# Load source spec
with open("$SPEC_FILE") as f:
    spec = yaml.safe_load(f)

# Load app's generated spec
import urllib.request
try:
    with urllib.request.urlopen("$APP_URL/api/openapi.json") as resp:
        app_spec = json.loads(resp.read())
except Exception as e:
    print(f"ERROR: Cannot reach app at $APP_URL/api/openapi.json: {e}")
    print("       Start the app first: uvicorn bookstore.main:app --port 8080")
    sys.exit(1)

errors = []

# Check all spec paths exist in app
spec_paths = set(spec.get("paths", {}).keys())
app_paths = {p.replace("/api", "", 1) for p in app_spec.get("paths", {}).keys()}

for path in spec_paths:
    if path not in app_paths:
        errors.append(f"MISSING PATH: {path} defined in spec but not in app")

# Check all spec operation IDs exist in app
spec_ops = {}
for path, methods in spec.get("paths", {}).items():
    for method, details in methods.items():
        if method == "parameters":
            continue
        op_id = details.get("operationId")
        if op_id:
            spec_ops[op_id] = f"{method.upper()} {path}"

app_ops = set()
for path, methods in app_spec.get("paths", {}).items():
    for method, details in methods.items():
        if method == "parameters":
            continue
        op_id = details.get("operationId")
        if op_id:
            app_ops.add(op_id)

for op_id, endpoint in spec_ops.items():
    if op_id not in app_ops:
        errors.append(f"MISSING OPERATION: {op_id} ({endpoint}) defined in spec but not in app")

# Check all spec schemas exist in app
# Known mappings: spec name -> app name (e.g., spec uses 'Book' for create, app uses 'BookCreate')
SCHEMA_ALIASES = {"Book": "BookCreate"}

spec_schemas = set(spec.get("components", {}).get("schemas", {}).keys())
app_schemas = set(app_spec.get("components", {}).get("schemas", {}).keys())

for schema in spec_schemas:
    app_name = SCHEMA_ALIASES.get(schema, schema)
    if app_name not in app_schemas:
        errors.append(f"MISSING SCHEMA: {schema} (expected as {app_name}) defined in spec but not in app")

if errors:
    print(f"VALIDATION FAILED - {len(errors)} contract violations:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"VALIDATION PASSED")
    print(f"  Paths:      {len(spec_paths)} spec / {len(app_paths)} app")
    print(f"  Operations: {len(spec_ops)} spec / {len(app_ops)} app")
    print(f"  Schemas:    {len(spec_schemas)} spec / {len(app_schemas)} app")
PYEOF
