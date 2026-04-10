# Agent Memory

> Project-specific learnings, edge cases, and corrections discovered during development.
>
> **Note:** General conventions are documented in `.cursor/rules/`. This file is for learnings NOT covered there.

## How to Use This File

Add entries here when you discover:

- Project-specific gotchas or edge cases
- Bugs that were fixed with non-obvious solutions
- Integration issues between libraries
- Environment-specific problems (CI, Docker, etc.)
- Patterns that deviate from standard rules for valid reasons

**Format:**

```markdown
### Topic: Short Description

**Problem:** What went wrong or was confusing

**Solution:** How it was fixed

**Context:** (Optional) Why this happened or when to watch for it
```

---

## Entries

*Add learnings as they are discovered during development.*

<!-- Example entry format:

### TestContainers: Docker API Version Mismatch in CI

**Problem:** Tests failed in CI with "Unsupported Docker API version" error

**Solution:** Set `DOCKER_HOST` environment variable explicitly in CI configuration

**Context:** CI agents use Docker 20.10.x which requires explicit socket path for Testcontainers compatibility

-->
