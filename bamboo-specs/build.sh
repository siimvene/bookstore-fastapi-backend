#!/bin/bash
set -aeo pipefail

# Enable debug mode only if bamboo_debug is set to "true"
if [[ "${bamboo_debug}" == "true" ]]; then
  set -x
fi

# ============================================================
# Testcontainers configuration (must be set before tests run)
# ============================================================
export DOCKER_HOST=unix:///var/run/docker.sock
export TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock

# Configure Docker image name and tag
DOCKER_IMAGE="${bamboo_dockerRegistry}/${bamboo_dockerOrg}/${bamboo_application}-backend"
DOCKER_TAG=$(echo "${bamboo_planRepository_branchName}-b${bamboo_buildNumber}" | sed "s/\/\|_\|\./-/g")

echo "=== Build pipeline starting ==="

# Install uv for fast dependency management
pip install --no-cache-dir uv

# Install project dependencies (including dev)
uv pip install --system ".[dev]"

# Generate models from OpenAPI spec (Contract-First)
echo "Generating models from OpenAPI spec..."
bash scripts/generate-models.sh

# Run code formatting check
echo "Checking code formatting..."
ruff format --check .

# Run linting
echo "Running linter..."
ruff check .

# Run type checking
echo "Running type checks..."
mypy src/

# Execute tests with coverage
if [[ "${bamboo_junit}" == "true" ]]; then
  echo "Running tests with coverage..."
  pytest \
    --cov \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --junitxml=test-results/results.xml \
    -v
fi

# Execute SonarQube code analysis
if [[ "${bamboo_sonarQube}" == "true" && "${bamboo_sonarStatusOk}" == "true" ]]; then
  set +x
  if [[ -z "${bamboo_repository_pr_key}" ]]; then
    sonar-scanner \
      -Dsonar.token="${bamboo_sonarTokenSecret}" \
      -Dsonar.branch.name="${bamboo_planRepository_branch}" \
      -Dsonar.projectVersion="${bamboo_planRepository_branch}" \
      -Dsonar.python.coverage.reportPaths=coverage.xml
  else
    sonar-scanner \
      -Dsonar.token="${bamboo_sonarTokenSecret}" \
      -Dsonar.pullrequest.key="${bamboo_repository_pr_key}" \
      -Dsonar.pullrequest.branch="${bamboo_repository_pr_sourceBranch}" \
      -Dsonar.pullrequest.base="${bamboo_repository_pr_targetBranch}" \
      -Dsonar.python.coverage.reportPaths=coverage.xml
  fi
  [[ "${bamboo_debug}" == "true" ]] && set -x
fi

echo "=== Build pipeline completed ==="
