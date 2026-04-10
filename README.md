# Bookstore FastAPI Backend

REST API for Bookstore Application built with Python 3.12 and FastAPI.

## Business Functions

| Operation | HTTP Method | Endpoint | Description |
| :-------- | :---------- | :------------------------- | :-------------------------------- |
| List | GET | `/api/books` | List all books |
| Create | POST | `/api/books` | Add a new book |
| Read | GET | `/api/books/{bookId}` | Get book by ID |
| Update | PUT | `/api/books/{bookId}` | Update an existing book |
| Delete | DELETE | `/api/books/{bookId}` | Delete a book |
| Find ISBN | GET | `/api/books/isbn/{isbn}` | Find book by ISBN |
| Find Author| GET | `/api/books/author/{author}`| Find books by author (paginated) |
| Health | GET | `/api/health` | Health check endpoint |

## Technical Features

- **Contract-First API** — Pydantic models generated from OpenAPI 3.0.3 spec via `datamodel-code-generator`
- **OAuth2/JWT** — Resource server with JWT token validation (RS256 via JWKS)
- **OpenTelemetry** — Distributed tracing with auto-instrumentation for FastAPI, SQLAlchemy, httpx
- **Database Retry** — Automatic retry with exponential backoff via tenacity
- **Audit Logging** — Structured audit trail matching Spring Boot format (correlationId, actor, client, result)
- **SQLAlchemy 2.0** — Async ORM with type-safe queries; optional model generation via `sqlacodegen`
- **Alembic** — Database schema migrations
- **Structured Logging** — JSON logging via structlog with request context (trace_id, span_id, userId, clientIp)
- **RFC 7807** — Problem Details for HTTP API error responses
- **Pydantic v2** — Request/response validation with camelCase alias generation
- **Testcontainers** — Integration tests with real PostgreSQL
- **85% Coverage Gate** — Line and branch coverage enforced via pytest-cov
- **Static Analysis** — Ruff (format + lint), mypy (strict), SonarQube
- **Security Scanning** — Trivy container image scanning in CI

## Architecture

```
Router (FastAPI) → Service → SQLAlchemy async session → PostgreSQL
```

## Technology Stack

| Component | Technology | Version |
| :---------------- | :-------------------------- | :------ |
| Language | Python | 3.12+ |
| Framework | FastAPI | latest |
| ORM | SQLAlchemy | 2.0+ |
| Database Driver | asyncpg | latest |
| Migrations | Alembic | latest |
| Validation | Pydantic | v2 |
| Security | PyJWT | latest |
| Retry | tenacity | latest |
| Logging | structlog | latest |
| Tracing | OpenTelemetry | latest |
| API Codegen | datamodel-code-generator | latest |
| DB Codegen | sqlacodegen | latest |
| Formatting/Lint | Ruff | latest |
| Type Checking | mypy (strict) | latest |
| Testing | pytest + pytest-asyncio | latest |
| Containers | Testcontainers | latest |
| Security Scan | Trivy | latest |
| Database | PostgreSQL | 15 |
| Package Manager | uv | latest |

## Project Structure

```
bookstore-fastapi-backend/
├── alembic/                    # Database migrations
│   ├── env.py                  # Async Alembic environment
│   └── versions/               # Migration scripts
├── bamboo-specs/               # CI/CD configuration
├── docs/                       # Documentation
├── src/
│   └── bookstore/
│       ├── main.py             # FastAPI app factory, lifespan
│       ├── config/             # Settings, database, security, retry
│       ├── models/             # SQLAlchemy models + Pydantic schemas
│       ├── api/                # Route handlers + dependencies
│       ├── service/            # Business logic
│       └── core/               # Shared infrastructure (exceptions, audit, logging, middleware)
├── tests/
│   ├── conftest.py             # Testcontainers, async fixtures
│   ├── integration/            # API integration tests (httpx + AsyncClient)
│   ├── unit/                   # Service unit tests (mocked DB)
│   └── security/               # JWT security tests
├── pyproject.toml              # Dependencies + tool configuration
├── docker-compose.yml          # Local PostgreSQL
├── Dockerfile                  # Production container
└── AGENTS.md                   # AI agent guidelines
```

## Development

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL and Testcontainers)
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd bookstore-fastapi-backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL
docker-compose up -d

# Run database migrations
alembic upgrade head

# Start development server
uvicorn bookstore.main:app --reload --port 8080
```

### Docker Setup with Colima (macOS)

If using Colima instead of Docker Desktop:

```bash
# Uncomment and set in .env:
DOCKER_HOST=unix:///Users/$USER/.colima/default/docker.sock
```

## Spec-Driven Development

The OpenAPI spec (`src/resources/swagger/openapi.yml`) is the **single source of truth** for the API contract.

```
openapi.yml (source of truth)
    │
    ├─ datamodel-code-generator → src/generated/openapi/models.py (generated Pydantic models)
    │                                    ↓
    │                            models/schemas.py (extends generated, adds ORM config + serializers)
    │                                    ↓
    │                            api/books.py (routes use schemas, path params match spec)
    │
    └─ scripts/validate-spec.sh → CI check: spec paths/operations/schemas match running app
```

**Workflow:**
1. Edit `openapi.yml` to define or change the API contract
2. Run `scripts/generate-models.sh` to regenerate Pydantic models
3. Extend generated models in `schemas.py` if needed (ORM support, serializers)
4. Implement business logic in service layer
5. Run `scripts/validate-spec.sh` to verify no contract drift

## Code Generation

| Generator | Input | Output | Command |
| :--- | :--- | :--- | :--- |
| API models | `src/resources/swagger/openapi.yml` | `src/generated/openapi/models.py` | `scripts/generate-models.sh` |
| DB models | Live PostgreSQL schema | `src/generated/db/models.py` | `scripts/generate-db-models.sh` |
| Spec validation | OpenAPI spec vs running app | Pass/fail | `scripts/validate-spec.sh` |

Generated code is excluded from formatting, linting, coverage, and SonarQube analysis.

## Commands

| Task | Command |
| :---------------------- | :------------------------------------------ |
| Run application | `uvicorn bookstore.main:app --reload` |
| Run tests | `pytest` |
| Run tests with coverage | `pytest --cov --cov-report=html` |
| Format code | `ruff format .` |
| Lint code | `ruff check .` |
| Fix lint issues | `ruff check --fix .` |
| Type check | `mypy src/` |
| Run migrations | `alembic upgrade head` |
| Create migration | `alembic revision --autogenerate -m "desc"` |
| Generate API models | `scripts/generate-models.sh` |
| Generate DB models | `scripts/generate-db-models.sh` |

## API Documentation

When `ENABLE_SWAGGER_UI=true` and `ENABLE_API_DOCS=true`:

- Swagger UI: `http://localhost:8080/api/docs`
- ReDoc: `http://localhost:8080/api/redoc`
- OpenAPI JSON: `http://localhost:8080/api/openapi.json`

## Testing Strategy

### Unit Tests
- Service layer with mocked database sessions
- Isolated, fast, no external dependencies
- Run: `pytest tests/unit/ -v`

### Integration Tests
- Full API tests via httpx AsyncClient
- Real PostgreSQL via Testcontainers
- Run: `pytest tests/integration/ -v`

### Security Tests
- JWT token validation
- Authentication/authorization flows
- Run: `pytest tests/security/ -v`

### Coverage
- Minimum 85% line coverage enforced
- View report: `pytest --cov --cov-report=html && open htmlcov/index.html`

## Environment Variables

| Variable | Default | Description |
| :---------------------- | :---------------------------------------- | :---------------------------------- |
| `DATASOURCE_URL` | `postgresql+asyncpg://...localhost:5432/bookstore` | Database connection URL |
| `DB_POOL_MAX_SIZE` | `5` | Connection pool max size |
| `SERVER_PORT` | `8080` | Application port |
| `OAUTH2_JWK_URI` | *(required)* | JWT verification key endpoint |
| `OAUTH2_ISSUER_URI` | *(required)* | JWT token issuer |
| `OAUTH2_AUDIENCE` | `bookstore-api` | Expected JWT audience |
| `ENABLE_SWAGGER_UI` | `false` | Enable Swagger UI |
| `ENABLE_API_DOCS` | `false` | Enable API docs and OpenAPI JSON |
| `LOG_LEVEL` | `INFO` | Root log level |
| `APP_LOG_LEVEL` | `DEBUG` | Application log level |
| `LOG_JSON` | `true` | Output JSON-formatted logs |
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry tracing |
| `OTEL_SERVICE_NAME` | `bookstore-service` | Service name in traces |
| `OTEL_EXPORTER_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |

## Git Workflow

### Branches
- `feature/description` — New features
- `fix/description` — Bug fixes
- `refactor/description` — Code improvements

### Commits
```
type(scope): description

feat(api): add search endpoint
fix(retry): handle connection timeout properly
refactor(service): extract mapping to dedicated methods
```

All commits must contain a ticket number.

