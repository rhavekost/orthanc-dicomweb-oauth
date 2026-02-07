#!/bin/bash
# Quality Check Script
# Runs all code quality checks for the Orthanc DICOMweb OAuth Plugin
#
# Usage: ./scripts/quality-check.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Run a check and track result
run_check() {
    local name="$1"
    shift
    local cmd=("$@")

    echo -e "${BLUE}▶ Running: ${name}${NC}"

    if "${cmd[@]}" 2>&1; then
        echo -e "${GREEN}✓ ${name} passed${NC}\n"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ ${name} failed${NC}\n"
        ((FAILED++))
        return 1
    fi
}

# Run a check that might be skipped
run_check_optional() {
    local name="$1"
    local tool="$2"
    shift 2
    local cmd=("$@")

    if ! command_exists "$tool"; then
        echo -e "${YELLOW}⊘ ${name} skipped (${tool} not installed)${NC}\n"
        ((SKIPPED++))
        return 0
    fi

    run_check "$name" "${cmd[@]}"
}

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Orthanc DICOMweb OAuth - Quality Checks     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# 1. Code Formatting
echo -e "${BLUE}═══ Code Formatting ═══${NC}"
run_check "black (formatting check)" black --check src/ tests/
run_check "isort (import sorting)" isort --check-only src/ tests/
echo ""

# 2. Linting
echo -e "${BLUE}═══ Linting ═══${NC}"
run_check "flake8" flake8 src/ tests/
run_check_optional "pylint" pylint pylint src/ --rcfile=pyproject.toml --fail-under=9.0
echo ""

# 3. Type Checking
echo -e "${BLUE}═══ Type Checking ═══${NC}"
run_check "mypy (strict mode)" mypy src/
echo ""

# 4. Security
echo -e "${BLUE}═══ Security ═══${NC}"
run_check "bandit (security scan)" bandit -r src/ -ll
echo ""

# 5. Code Quality Metrics
echo -e "${BLUE}═══ Code Quality Metrics ═══${NC}"
run_check_optional "radon (complexity)" radon radon cc src/ -a --total-average
run_check_optional "vulture (dead code)" vulture vulture src/ --min-confidence 80
echo ""

# 6. Documentation
echo -e "${BLUE}═══ Documentation ═══${NC}"
run_check_optional "pydocstyle" pydocstyle pydocstyle --convention=google --add-ignore=D105,D107,D102,D212 src/
echo ""

# 7. Tests
echo -e "${BLUE}═══ Tests ═══${NC}"
run_check "pytest (with coverage)" pytest tests/ --cov=src --cov-report=term --cov-fail-under=80
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    SUMMARY                     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ Passed:  ${PASSED}${NC}"
echo -e "${RED}✗ Failed:  ${FAILED}${NC}"
echo -e "${YELLOW}⊘ Skipped: ${SKIPPED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ALL QUALITY CHECKS PASSED! ✓          ║${NC}"
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║       QUALITY CHECKS FAILED: ${FAILED} issue(s)          ║${NC}"
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo ""
    echo "Please fix the issues above and re-run the checks."
    echo "See docs/CODING-STANDARDS.md for guidelines."
    echo ""
    exit 1
fi
