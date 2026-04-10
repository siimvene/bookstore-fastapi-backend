#!/bin/bash
set -aeo pipefail

# Configure Docker image name and tag
DOCKER_IMAGE="${bamboo_dockerRegistry}/${bamboo_dockerOrg}/${bamboo_application}-backend"
DOCKER_TAG=$(echo "${bamboo_planRepository_branchName}-b${bamboo_buildNumber}" | sed "s/\/\|_\|\./-/g")

echo "=== Docker build pipeline starting ==="

echo "Building Docker image ${DOCKER_IMAGE}:${DOCKER_TAG}"
docker build --tag "${DOCKER_IMAGE}:${DOCKER_TAG}" .

# Run Trivy security scan
if [[ "${bamboo_trivy}" == "true" ]]; then
    echo "Running Trivy security scan..."
    trivy image --severity HIGH,CRITICAL --exit-code 1 "${DOCKER_IMAGE}:${DOCKER_TAG}"
fi

# Only publish if:
# 1. publishFeatureBranches is true OR
# 2. Branch is not a feature branch (e.g., release/*, hotfix/*, develop, main)
if [[ "${bamboo_publishFeatureBranches}" == "true" || ! "${bamboo_planRepository_branch,,}" =~ ^feature/* ]]; then
    echo "Pushing Docker image ${DOCKER_IMAGE}:${DOCKER_TAG}"
    docker push "${DOCKER_IMAGE}:${DOCKER_TAG}"
else
    echo "Skipping Docker push for feature branch"
fi

echo "Cleaning up dangling Docker images"
docker image prune --all --force

echo "=== Docker build pipeline completed ==="
