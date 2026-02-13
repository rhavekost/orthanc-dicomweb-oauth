#!/bin/bash
# Integration test script for orthanc-dicomweb-oauth
# Tests the plugin with a real Orthanc instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Orthanc DICOMweb OAuth Integration Test ===${NC}"

# Check prerequisites
command -v docker >/dev/null 2>&1 || {
    echo -e "${RED}Error: docker is required but not installed${NC}" >&2
    exit 1
}

command -v curl >/dev/null 2>&1 || {
    echo -e "${RED}Error: curl is required but not installed${NC}" >&2
    exit 1
}

# Configuration
ORTHANC_PORT=8042
CONTAINER_NAME="orthanc-oauth-integration-test"
MAX_WAIT=30

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
    docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
}

# Register cleanup on exit
trap cleanup EXIT

# Stop any existing container
cleanup

echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -f docker/Dockerfile -t orthanc-oauth-test:latest .

echo -e "${YELLOW}Step 2: Starting Orthanc container...${NC}"
docker run -d \
    --name $CONTAINER_NAME \
    -p $ORTHANC_PORT:8042 \
    -e OAUTH_CLIENT_ID=test-client \
    -e OAUTH_CLIENT_SECRET=test-secret \
    orthanc-oauth-test:latest

echo -e "${YELLOW}Step 3: Waiting for Orthanc to be ready...${NC}"
WAITED=0
while ! curl -s -u orthanc:orthanc http://localhost:$ORTHANC_PORT/app/explorer.html >/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}Error: Orthanc failed to start within ${MAX_WAIT}s${NC}"
        docker logs $CONTAINER_NAME
        exit 1
    fi
    echo -n "."
    sleep 1
    WAITED=$((WAITED + 1))
done
echo -e " ${GREEN}Ready!${NC}"

echo -e "${YELLOW}Step 4: Testing plugin REST API endpoints...${NC}"

# Test /dicomweb-oauth/status endpoint
echo -n "  - Testing /dicomweb-oauth/status... "
STATUS_RESPONSE=$(curl -s -u orthanc:orthanc http://localhost:$ORTHANC_PORT/dicomweb-oauth/status)
if echo "$STATUS_RESPONSE" | grep -q '"status"'; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $STATUS_RESPONSE"
    echo -e "${YELLOW}Orthanc logs:${NC}"
    docker logs $CONTAINER_NAME 2>&1 | tail -50
    exit 1
fi

# Test server configuration
echo -n "  - Verifying server configuration... "
if echo "$STATUS_RESPONSE" | grep -q '"servers_configured"'; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Response: $STATUS_RESPONSE"
    exit 1
fi

# Verify token preview is NOT exposed (security fix)
echo -n "  - Verifying token privacy... "
if echo "$STATUS_RESPONSE" | grep -q 'token_preview'; then
    echo -e "${RED}✗ SECURITY ISSUE: token_preview found in response${NC}"
    exit 1
else
    echo -e "${GREEN}✓${NC}"
fi

echo -e "${YELLOW}Step 5: Checking plugin logs...${NC}"
docker logs $CONTAINER_NAME 2>&1 | tail -20

echo -e "${GREEN}=== All integration tests passed! ===${NC}"
exit 0
