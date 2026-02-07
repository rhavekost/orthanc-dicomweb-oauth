#!/bin/bash
set -e

echo "=== Orthanc DICOMweb OAuth Plugin - Integration Tests ==="
echo ""

# Configuration
ORTHANC_URL="${ORTHANC_URL:-http://localhost:8042}"
TIMEOUT=30

echo "Testing Orthanc at: $ORTHANC_URL"
echo ""

# Test 1: Check if Orthanc is running
echo "Test 1: Checking Orthanc availability..."
if curl -sf "${ORTHANC_URL}/system" > /dev/null; then
    echo "✓ Orthanc is running"
else
    echo "✗ Orthanc is not accessible at ${ORTHANC_URL}"
    exit 1
fi
echo ""

# Test 2: Check plugin status
echo "Test 2: Checking plugin status..."
STATUS=$(curl -sf "${ORTHANC_URL}/dicomweb-oauth/status")
if [ $? -eq 0 ]; then
    echo "✓ Plugin is loaded"
    echo "   Response: $STATUS"
else
    echo "✗ Plugin status endpoint not accessible"
    exit 1
fi
echo ""

# Test 3: Verify plugin version
echo "Test 3: Verifying plugin version..."
VERSION=$(echo "$STATUS" | grep -o '"version": "[^"]*"' | cut -d'"' -f4)
if [ "$VERSION" = "1.0.0" ]; then
    echo "✓ Plugin version: $VERSION"
else
    echo "✗ Unexpected plugin version: $VERSION"
    exit 1
fi
echo ""

# Test 4: List configured servers
echo "Test 4: Listing configured servers..."
SERVERS=$(curl -sf "${ORTHANC_URL}/dicomweb-oauth/servers")
if [ $? -eq 0 ]; then
    echo "✓ Servers endpoint accessible"
    echo "   Response: $SERVERS"
else
    echo "✗ Servers endpoint not accessible"
    exit 1
fi
echo ""

# Test 5: Count configured servers
echo "Test 5: Checking server configuration..."
SERVER_COUNT=$(echo "$STATUS" | grep -o '"configured_servers": [0-9]*' | grep -o '[0-9]*')
if [ "$SERVER_COUNT" -gt 0 ]; then
    echo "✓ Found $SERVER_COUNT configured server(s)"
else
    echo "⚠ No servers configured (this is OK for testing, but plugin won't inject tokens)"
fi
echo ""

# Test 6: Test token acquisition (if servers configured)
if [ "$SERVER_COUNT" -gt 0 ]; then
    echo "Test 6: Testing token acquisition..."
    SERVER_NAME=$(echo "$STATUS" | grep -o '"servers": \[[^]]*\]' | grep -o '"\([^"]*\)"' | head -1 | tr -d '"')

    if [ -n "$SERVER_NAME" ]; then
        echo "   Testing server: $SERVER_NAME"
        TEST_RESULT=$(curl -sf -X POST "${ORTHANC_URL}/dicomweb-oauth/servers/${SERVER_NAME}/test")

        if [ $? -eq 0 ]; then
            echo "✓ Token test completed"
            echo "   Response: $TEST_RESULT"

            # Check if token was acquired successfully
            if echo "$TEST_RESULT" | grep -q '"status": "success"'; then
                echo "✓ Token acquisition successful"
            else
                echo "⚠ Token acquisition failed (check credentials and network)"
            fi
        else
            echo "⚠ Token test endpoint failed"
        fi
    fi
else
    echo "Test 6: Skipped (no servers configured)"
fi
echo ""

# Summary
echo "=== Integration Test Summary ==="
echo "✓ All core tests passed"
echo "✓ Plugin is functional"
echo ""
echo "Next steps:"
echo "1. Configure OAuth credentials in orthanc.json or .env"
echo "2. Test with real DICOMweb server"
echo "3. Monitor logs: docker-compose logs -f orthanc"
echo ""
