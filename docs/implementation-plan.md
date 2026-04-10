# Implementation Plan: Closing Spring Boot ↔ FastAPI Gaps

Cross-reference analysis identified 7 gaps between the Spring Boot reference implementation
(`bookstore-boot-backend`) and the FastAPI implementation (`bookstore-fastapi-backend`).

## Status Overview

| # | Gap | Tool | Effort | Status |
|---|---|---|---|---|
| 1 | Contract-First API models from OpenAPI | `datamodel-code-generator` | Large | DONE |
| 2 | Enriched audit logging (structured DTO) | Pydantic DTO + contextvars | Medium | DONE |
| 3 | Middleware enrichment (userId, clientIp) | structlog contextvars | Low | DONE |
| 4 | Branch coverage gate | pyproject.toml config | Low | DONE |
| 5 | mypy type checking in CI | mypy + build.sh | Low | DONE |
| 6 | Security scanning | Trivy | Low | DONE |
| 7 | DB model generation from schema | `sqlacodegen` | Medium | DONE |

## Implementation Order

```
Gap 3 (middleware)        → do first, gaps 2 depends on it
Gap 2 (audit logging)     → depends on gap 3 (needs userId/clientIp in context)
Gap 4 (branch coverage)   → independent, quick
Gap 5 (mypy in CI)        → independent, quick
Gap 6 (Trivy)             → independent, quick
Gap 7 (sqlacodegen)       → independent, medium
Gap 1 (contract-first)    → independent, largest change
```

---

## Gap 1: Contract-First OpenAPI Code Generation

**Problem**: FastAPI project is Code-First (generates OpenAPI spec from code). Spring Boot uses
Contract-First (OpenAPI spec → generated controller interfaces + models via `openapi-generator`).

**Tool**: `datamodel-code-generator` v0.56+ (tested, generates Pydantic v2 models with aliases,
field constraints, and examples from OpenAPI 3.0.3 spec).

**Steps**:
1. Copy `openapi.yml` to `src/resources/swagger/openapi.yml`
2. Add `datamodel-code-generator` as dev dependency in `pyproject.toml`
3. Create `scripts/generate-models.sh`:
   ```bash
   datamodel-codegen \
     --input src/resources/swagger/openapi.yml \
     --input-file-type openapi \
     --output-model-type pydantic_v2.BaseModel \
     --use-field-description --field-constraints --use-default \
     --snake-case-field --target-python-version 3.12 \
     --output src/generated/openapi/models.py
   ```
4. Create `src/generated/` directory with `__init__.py`
5. Refactor `models/schemas.py` to import from generated models, extend with `from_attributes`,
   `CamelModel` base, `field_serializer`
6. Update SonarQube config to exclude `src/generated/`
7. Add generate step to `bamboo-specs/build.sh` before tests

**Spring Boot parallel**:
- `openapi-generator` (spring, delegatePattern=true) → `src/generated/java/openapi/`
- `datamodel-code-generator` → `src/generated/openapi/`

---

## Gap 2: Enriched Audit Logging

**Problem**: Current `AuditLogger` uses flat static methods with minimal context. Spring Boot emits
a rich structured DTO with 7 sections: correlationId, time, application, activity, actor, client, result.

**Approach**: Pydantic `AuditLog` DTO + read from structlog contextvars. Zero call-site changes.

**Steps**:
1. Create `src/bookstore/core/audit_models.py` with Pydantic models:
   - `AuditLog` (top-level): correlationId, time, application, activity, actor, client, result
   - Nested: `AuditApplication`, `AuditActivity`, `AuditActor`, `AuditClient`, `AuditResult`
2. Add `environment` and `audit_client_id` fields to `Settings` class
3. Rewrite `AuditLogger` to build `AuditLog` DTO, reading `request_id`, `client_ip`, `user_id`
   from structlog contextvars automatically
4. Preserve static method signatures for backward compatibility — no changes to `book_service.py`

---

## Gap 3: Request Context Enrichment (userId + clientIp)

**Problem**: Middleware only binds `request_id`, `method`, `path` to structlog context.
Spring Boot binds `trace_id`, `userId`, `clientIp`, `sessionId`, `applicationName`.

**Approach**: Hybrid — clientIp in middleware (available from ASGI scope), userId in security
dependency (piggybacks on existing JWT validation).

**Steps**:
1. In `middleware.py`: extract `client_ip` from `X-Forwarded-For` header or `request.client.host`,
   bind to `structlog.contextvars`
2. In `security.py`: after successful `decode_token` in `get_current_user`, bind
   `user_id=payload.get("sub", "anonymous")` to `structlog.contextvars`
3. Optional: add lightweight JWT peek in middleware for `user_id` on unauthenticated endpoints

---

## Gap 4: Branch Coverage Gate

**Problem**: Only line coverage (85%) enforced. Spring Boot enforces 65% branch coverage too.

**Steps**:
1. In `pyproject.toml`:
   ```toml
   [tool.coverage.run]
   branch = true

   [tool.coverage.report]
   fail_under = 85
   ```

---

## Gap 5: mypy Type Checking in CI

**Problem**: mypy available but not enforced in CI pipeline. Spring Boot gets compile-time type
safety from Java compiler.

**Steps**:
1. Add mypy to dev dependencies in `pyproject.toml`
2. Add `[tool.mypy]` config:
   ```toml
   [tool.mypy]
   python_version = "3.12"
   strict = true
   exclude = ["src/generated/"]
   ```
3. Add `mypy src/` step in `bamboo-specs/build.sh` after ruff checks

---

## Gap 6: Security Scanning (Trivy)

**Problem**: Spring Boot pipeline has Trivy + JFrog X-Ray. FastAPI pipeline has neither.

**Steps**:
1. Add `trivy: true` variable in `bamboo-specs/bamboo.yml`
2. Add Trivy scan step in Docker stage:
   ```bash
   trivy image --severity HIGH,CRITICAL --exit-code 1 ${image}:${tag}
   ```

---

## Gap 7: DB Model Generation from Schema

**Problem**: Spring Boot uses jOOQ to generate type-safe DB record classes from live schema.
FastAPI has manually written SQLAlchemy models.

**Tool**: `sqlacodegen` v4.0.3 (generates SQLAlchemy 2.0 `Mapped` declarative classes from DB).

**Steps**:
1. Add `sqlacodegen` as dev dependency
2. Create `scripts/generate-db-models.sh`:
   ```bash
   sqlacodegen \
     --generator declarative \
     --tables book \
     --outfile src/generated/db/models.py \
     ${DATASOURCE_URL}
   ```
3. Output to `src/generated/db/`, exclude from formatting/coverage/SonarQube
4. Hand-written model in `models/book.py` imports/extends from generated base

**Spring Boot parallel**:
- jOOQ → `src/generated/java/jooq/` (package `com.example.jooq`)
- sqlacodegen → `src/generated/db/`

---

## Cross-Reference: Spring Boot ↔ FastAPI Equivalents

| Spring Boot | FastAPI Equivalent |
|---|---|
| `openapi-generator` (spring) | `datamodel-code-generator` |
| jOOQ codegen | `sqlacodegen` |
| Flyway | Alembic |
| Spring Security OAuth2 Resource Server | PyJWT + JWKClient |
| Spring RetryTemplate + AbstractDatabaseService | tenacity `@db_retry` |
| HikariCP SQLExceptionOverride | Recoverable SQLStates in retry config |
| Logstash JSON encoder + MDC | structlog JSONRenderer + contextvars |
| AuditLogger + AuditLog DTO | AuditLogger + AuditLog Pydantic model |
| JaCoCo (85% line, 65% branch) | pytest-cov (85% line + branch) |
| Spotless (Google Java Format) | Ruff format |
| SonarQube | SonarQube |
| Trivy + JFrog X-Ray | Trivy |
| Java compiler | mypy --strict |
| `@ConfigurationProperties` | Pydantic `BaseSettings` |
| `@ControllerAdvice` + Problem Details | ProblemDetail exception + handlers |
| Testcontainers (singleton reuse) | Testcontainers (session-scoped) |
