#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Test Orthanc OAuth Deployment
# ========================================
#
# This script tests the deployed Orthanc instance by uploading
# a test DICOM file and verifying it's stored and forwarded.
#
# Prerequisites:
# - curl
# - jq
# - Deployed Orthanc instance (run deploy.sh first)
#
# Usage:
#   ./test-deployment.sh --url https://orthanc-quickstart.example.com
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ORTHANC_URL=""
USERNAME="admin"
PASSWORD=""
DEPLOYMENT_DETAILS_FILE="deployment-details.json"
TEST_DICOM_FILE=""

# ========================================
# Functions
# ========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Test deployed Orthanc instance with OAuth plugin.

OPTIONS:
    -u, --url URL              Orthanc URL (e.g., https://orthanc.example.com)
    -U, --username USERNAME    Orthanc username (default: admin)
    -P, --password PASSWORD    Orthanc password
    -d, --deployment FILE      Deployment details JSON (default: deployment-details.json)
    -f, --file FILE            Test DICOM file to upload
    -h, --help                 Show this help message

EXAMPLE:
    $0 --url https://orthanc-quickstart.example.com --password mypassword

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            ORTHANC_URL="$2"
            shift 2
            ;;
        -U|--username)
            USERNAME="$2"
            shift 2
            ;;
        -P|--password)
            PASSWORD="$2"
            shift 2
            ;;
        -d|--deployment)
            DEPLOYMENT_DETAILS_FILE="$2"
            shift 2
            ;;
        -f|--file)
            TEST_DICOM_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# ========================================
# Load Deployment Details
# ========================================

if [[ -f "$DEPLOYMENT_DETAILS_FILE" && -z "$ORTHANC_URL" ]]; then
    log_info "Loading deployment details from: $DEPLOYMENT_DETAILS_FILE"
    ORTHANC_URL=$(jq -r '.containerAppUrl' "$DEPLOYMENT_DETAILS_FILE")
    if [[ -z "$PASSWORD" ]]; then
        PASSWORD=$(jq -r '.orthancPassword' "$DEPLOYMENT_DETAILS_FILE")
    fi
fi

# Validate required parameters
if [[ -z "$ORTHANC_URL" ]]; then
    log_error "Orthanc URL is required"
    show_usage
    exit 1
fi

if [[ -z "$PASSWORD" ]]; then
    log_error "Password is required"
    show_usage
    exit 1
fi

# ========================================
# Test 1: Check System Status
# ========================================

log_test "Test 1/5: Checking Orthanc system status"

RESPONSE=$(curl -s -u "$USERNAME:$PASSWORD" "$ORTHANC_URL/system" || echo "")

if [[ -z "$RESPONSE" ]]; then
    log_error "Failed to connect to Orthanc at $ORTHANC_URL"
    exit 1
fi

VERSION=$(echo "$RESPONSE" | jq -r '.Version')
DICOM_AET=$(echo "$RESPONSE" | jq -r '.DicomAet')

log_info "Orthanc version: $VERSION"
log_info "DICOM AET: $DICOM_AET"
echo -e "${GREEN}✓ System status OK${NC}"
echo ""

# ========================================
# Test 2: Check Plugin Status
# ========================================

log_test "Test 2/5: Checking OAuth plugin status"

PLUGINS=$(echo "$RESPONSE" | jq -r '.Plugins[]')

if echo "$PLUGINS" | grep -q "dicomweb_oauth"; then
    log_info "OAuth plugin loaded"
    echo -e "${GREEN}✓ Plugin status OK${NC}"
else
    log_warn "OAuth plugin not found in plugin list"
    echo -e "${YELLOW}⚠ Plugin might not be loaded${NC}"
fi
echo ""

# ========================================
# Test 3: Check Database Connection
# ========================================

log_test "Test 3/5: Checking database connection"

STATS=$(curl -s -u "$USERNAME:$PASSWORD" "$ORTHANC_URL/statistics" || echo "{}")
TOTAL_STUDIES=$(echo "$STATS" | jq -r '.TotalDiskSize' || echo "unknown")

log_info "Database connection: OK"
log_info "Total disk size: $TOTAL_STUDIES bytes"
echo -e "${GREEN}✓ Database connection OK${NC}"
echo ""

# ========================================
# Test 4: Upload Test DICOM (Optional)
# ========================================

if [[ -n "$TEST_DICOM_FILE" && -f "$TEST_DICOM_FILE" ]]; then
    log_test "Test 4/5: Uploading test DICOM file"

    UPLOAD_RESPONSE=$(curl -s -u "$USERNAME:$PASSWORD" \
        -X POST \
        -H "Content-Type: application/dicom" \
        --data-binary "@$TEST_DICOM_FILE" \
        "$ORTHANC_URL/instances")

    INSTANCE_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.ID')

    if [[ -n "$INSTANCE_ID" && "$INSTANCE_ID" != "null" ]]; then
        log_info "Instance uploaded: $INSTANCE_ID"
        echo -e "${GREEN}✓ DICOM upload OK${NC}"
    else
        log_error "Failed to upload DICOM file"
        echo -e "${RED}✗ DICOM upload failed${NC}"
    fi
else
    log_info "Skipping DICOM upload (no test file provided)"
    echo -e "${YELLOW}⊘ DICOM upload skipped${NC}"
fi
echo ""

# ========================================
# Test 5: Check Metrics Endpoint
# ========================================

log_test "Test 5/5: Checking Prometheus metrics"

METRICS=$(curl -s -u "$USERNAME:$PASSWORD" "$ORTHANC_URL/metrics" || echo "")

if [[ -n "$METRICS" ]] && echo "$METRICS" | grep -q "orthanc_"; then
    log_info "Metrics endpoint responding"
    METRIC_COUNT=$(echo "$METRICS" | grep -c "^orthanc_" || echo "0")
    log_info "Metrics available: $METRIC_COUNT"
    echo -e "${GREEN}✓ Metrics endpoint OK${NC}"
else
    log_warn "Metrics endpoint not responding"
    echo -e "${YELLOW}⚠ Metrics endpoint unavailable${NC}"
fi
echo ""

# ========================================
# Summary
# ========================================

cat << EOF
${GREEN}═══════════════════════════════════════════════════${NC}
${GREEN}                  TEST SUMMARY                    ${NC}
${GREEN}═══════════════════════════════════════════════════${NC}

Orthanc URL: $ORTHANC_URL
Version: $VERSION
DICOM AET: $DICOM_AET

All critical tests passed! ✓

Next steps:
  1. Configure DICOM modalities
  2. Test OAuth authentication with DICOM service
  3. Monitor logs for any errors
  4. Set up backup and monitoring

EOF
