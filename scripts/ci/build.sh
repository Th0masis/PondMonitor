#!/bin/bash
# Docker build script for CI/CD pipeline

set -e

# Change to project root
cd "$(dirname "$0")/../.."

echo "🏗️ Building PondMonitor Docker Images"
echo "====================================="

# Configuration
REGISTRY="${REGISTRY:-ghcr.io}"
REPO_NAME="${GITHUB_REPOSITORY:-pondmonitor}"
VERSION="${GITHUB_REF_NAME:-latest}"
PLATFORM="${PLATFORM:-linux/amd64,linux/arm64}"

# Clean version tag (remove 'v' prefix if present)
if [[ $VERSION == v* ]]; then
    VERSION=${VERSION#v}
fi

echo "📋 Build Configuration:"
echo "  Registry: $REGISTRY"
echo "  Repository: $REPO_NAME"
echo "  Version: $VERSION"
echo "  Platform: $PLATFORM"
echo ""

# Check Docker and Buildx
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! docker buildx version &> /dev/null; then
    echo "❌ Docker Buildx is not available"
    exit 1
fi

# Setup buildx builder if not exists
if ! docker buildx ls | grep -q "pondmonitor-builder"; then
    echo "🔧 Creating buildx builder..."
    docker buildx create --name pondmonitor-builder --use
    docker buildx inspect --bootstrap
else
    echo "✅ Using existing buildx builder"
    docker buildx use pondmonitor-builder
fi

# Build Flask UI image
echo "🐳 Building Flask UI image..."
docker buildx build \
    --platform ${PLATFORM} \
    --file docker/dockerfile.flask_ui \
    --tag ${REGISTRY}/${REPO_NAME}/flask-ui:${VERSION} \
    --tag ${REGISTRY}/${REPO_NAME}/flask-ui:latest \
    --cache-from type=gha \
    --cache-to type=gha,mode=max \
    ${PUSH:+--push} \
    .

# Build LoRa Gateway image
echo "🐳 Building LoRa Gateway image..."
docker buildx build \
    --platform ${PLATFORM} \
    --file docker/dockerfile.gateway \
    --tag ${REGISTRY}/${REPO_NAME}/lora-gateway:${VERSION} \
    --tag ${REGISTRY}/${REPO_NAME}/lora-gateway:latest \
    --cache-from type=gha \
    --cache-to type=gha,mode=max \
    ${PUSH:+--push} \
    .

# Local testing build (single platform)
if [ "$LOCAL_TEST" = "true" ]; then
    echo "🧪 Building local test images..."
    docker build \
        --file docker/dockerfile.flask_ui \
        --tag pondmonitor-flask-ui:test \
        .
    
    docker build \
        --file docker/dockerfile.gateway \
        --tag pondmonitor-gateway:test \
        .
    
    echo "✅ Local test images built successfully"
fi

# Validate images
if [ "$VALIDATE" = "true" ]; then
    echo "🔍 Validating built images..."
    
    # Basic image inspection
    docker buildx imagetools inspect ${REGISTRY}/${REPO_NAME}/flask-ui:${VERSION} || true
    docker buildx imagetools inspect ${REGISTRY}/${REPO_NAME}/lora-gateway:${VERSION} || true
    
    # Security scan with Trivy (if available)
    if command -v trivy &> /dev/null; then
        echo "🔒 Running security scan..."
        trivy image --exit-code 0 ${REGISTRY}/${REPO_NAME}/flask-ui:${VERSION} || true
        trivy image --exit-code 0 ${REGISTRY}/${REPO_NAME}/lora-gateway:${VERSION} || true
    fi
fi

echo ""
echo "✅ Docker images built successfully!"
echo "📦 Images available:"
echo "  - ${REGISTRY}/${REPO_NAME}/flask-ui:${VERSION}"
echo "  - ${REGISTRY}/${REPO_NAME}/lora-gateway:${VERSION}"

if [ -n "$GITHUB_STEP_SUMMARY" ]; then
    echo "## 🐳 Docker Build Summary" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "### Built Images:" >> $GITHUB_STEP_SUMMARY
    echo "- \`${REGISTRY}/${REPO_NAME}/flask-ui:${VERSION}\`" >> $GITHUB_STEP_SUMMARY
    echo "- \`${REGISTRY}/${REPO_NAME}/lora-gateway:${VERSION}\`" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "### Platforms:" >> $GITHUB_STEP_SUMMARY
    echo "- $PLATFORM" >> $GITHUB_STEP_SUMMARY
fi