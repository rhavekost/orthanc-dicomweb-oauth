#!/usr/bin/env bash
set -euo pipefail

# ========================================
# Upload Synthetic DICOM Test Data
# ========================================
#
# Uploads synthetic test data to deployed Orthanc instance
#
# Usage:
#   ./upload-test-data.sh --url https://orthanc.example.com --password secret
#   ./upload-test-data.sh --deployment-dir ../quickstart
#   ./upload-test-data.sh --deployment-dir ../production
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Variables
ORTHANC_URL=""
ORTHANC_PASSWORD=""
ORTHANC_USERNAME="admin"
DEPLOYMENT_DIR=""
TEST_DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/sample-study" && pwd)"

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

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Upload synthetic DICOM test data to Orthanc deployment.

OPTIONS:
    --url URL                    Orthanc URL (e.g., https://orthanc.example.com)
    --password PASSWORD          Orthanc admin password
    --username USERNAME          Orthanc admin username (default: admin)
    --deployment-dir DIR         Auto-detect URL and password from deployment-details.json
    -h, --help                   Show this help message

EXAMPLES:
    # Manual URL and password
    $0 --url https://orthanc-quickstart-app.example.com --password mypassword

    # Auto-detect from quickstart deployment
    $0 --deployment-dir ../quickstart

    # Auto-detect from production deployment
    $0 --deployment-dir ../production

EOF
}

# ========================================
# Parse Arguments
# ========================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            ORTHANC_URL="$2"
            shift 2
            ;;
        --password)
            ORTHANC_PASSWORD="$2"
            shift 2
            ;;
        --username)
            ORTHANC_USERNAME="$2"
            shift 2
            ;;
        --deployment-dir)
            DEPLOYMENT_DIR="$2"
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
# Auto-detect from deployment directory
# ========================================

if [[ -n "$DEPLOYMENT_DIR" ]]; then
    DETAILS_FILE="$DEPLOYMENT_DIR/deployment-details.json"

    if [[ ! -f "$DETAILS_FILE" ]]; then
        log_error "deployment-details.json not found in $DEPLOYMENT_DIR"
        log_error "Run deploy.sh first to create deployment"
        exit 1
    fi

    log_info "Reading deployment details from $DETAILS_FILE"

    ORTHANC_URL=$(jq -r '.containerAppUrl' "$DETAILS_FILE")
    ORTHANC_PASSWORD=$(jq -r '.orthancPassword' "$DETAILS_FILE")

    if [[ -z "$ORTHANC_URL" || "$ORTHANC_URL" == "null" ]]; then
        log_error "Could not read containerAppUrl from deployment-details.json"
        exit 1
    fi

    if [[ -z "$ORTHANC_PASSWORD" || "$ORTHANC_PASSWORD" == "null" ]]; then
        log_error "Could not read orthancPassword from deployment-details.json"
        exit 1
    fi

    # Add https:// if not present
    if [[ ! "$ORTHANC_URL" =~ ^https?:// ]]; then
        ORTHANC_URL="https://$ORTHANC_URL"
    fi
fi

# ========================================
# Validate Parameters
# ========================================

if [[ -z "$ORTHANC_URL" ]]; then
    log_error "Orthanc URL is required (--url or --deployment-dir)"
    show_usage
    exit 1
fi

if [[ -z "$ORTHANC_PASSWORD" ]]; then
    log_error "Orthanc password is required (--password or --deployment-dir)"
    show_usage
    exit 1
fi

# ========================================
# Check Test Data Exists
# ========================================

if [[ ! -d "$TEST_DATA_DIR" ]]; then
    log_error "Test data directory not found: $TEST_DATA_DIR"
    log_error "Generate test data first: python3 generate-synthetic-dicom.py"
    exit 1
fi

DICOM_FILES=("$TEST_DATA_DIR"/*.dcm)
if [[ ! -e "${DICOM_FILES[0]}" ]]; then
    log_error "No DICOM files found in $TEST_DATA_DIR"
    log_error "Generate test data first: python3 generate-synthetic-dicom.py"
    exit 1
fi

FILE_COUNT=$(find "$TEST_DATA_DIR" -name "*.dcm" | wc -l)
log_info "Found $FILE_COUNT DICOM files to upload"

# ========================================
# Test Orthanc Connection
# ========================================

log_info "Testing connection to Orthanc at $ORTHANC_URL"

if ! curl -sf -u "$ORTHANC_USERNAME:$ORTHANC_PASSWORD" "$ORTHANC_URL/system" > /dev/null; then
    log_error "Failed to connect to Orthanc"
    log_error "Check URL and credentials"
    exit 1
fi

log_info "Connection successful"

# ========================================
# Upload DICOM Files
# ========================================

log_info "Uploading DICOM files..."

UPLOADED=0
FAILED=0

for dcm_file in "$TEST_DATA_DIR"/*.dcm; do
    filename=$(basename "$dcm_file")

    if curl -sf -X POST \
        -u "$ORTHANC_USERNAME:$ORTHANC_PASSWORD" \
        --data-binary @"$dcm_file" \
        "$ORTHANC_URL/instances" > /dev/null; then
        echo "  ✓ $filename"
        ((UPLOADED++))
    else
        echo "  ✗ $filename"
        ((FAILED++))
    fi
done

echo ""

# ========================================
# Summary
# ========================================

if [[ $FAILED -eq 0 ]]; then
    log_info "${GREEN}✅ Successfully uploaded $UPLOADED DICOM files${NC}"
else
    log_warn "Uploaded $UPLOADED files, $FAILED failed"
fi

# Get study information
log_info "Fetching study information..."
STUDIES=$(curl -sf -u "$ORTHANC_USERNAME:$ORTHANC_PASSWORD" "$ORTHANC_URL/studies")
STUDY_COUNT=$(echo "$STUDIES" | jq -r '. | length')

log_info "Total studies in Orthanc: $STUDY_COUNT"

if [[ $STUDY_COUNT -gt 0 ]]; then
    STUDY_ID=$(echo "$STUDIES" | jq -r '.[0]')
    STUDY_INFO=$(curl -sf -u "$ORTHANC_USERNAME:$ORTHANC_PASSWORD" "$ORTHANC_URL/studies/$STUDY_ID")
    PATIENT_NAME=$(echo "$STUDY_INFO" | jq -r '.PatientMainDicomTags.PatientName // "Unknown"')
    SERIES_COUNT=$(echo "$STUDY_INFO" | jq -r '.Series | length')

    echo ""
    echo "Latest study:"
    echo "  Patient: $PATIENT_NAME"
    echo "  Series: $SERIES_COUNT"
    echo "  Study URL: $ORTHANC_URL/app/explorer.html#study?uuid=$STUDY_ID"
fi

echo ""
log_info "Next steps:"
echo "  1. View in Orthanc: $ORTHANC_URL/app/explorer.html"
echo "  2. Test DICOM-web: curl -u $ORTHANC_USERNAME:*** $ORTHANC_URL/dicom-web/studies"
echo "  3. Verify OAuth forwarding to Azure DICOM service"
