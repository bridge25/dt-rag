#!/bin/bash
# MyPy Type Safety Progress Tracker
# Usage: bash .moai/scripts/mypy-progress.sh [--verbose]

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SPEC_DIR=".moai/specs/SPEC-MYPY-CONSOLIDATION-002"
HISTORY_FILE="${SPEC_DIR}/mypy-history.txt"
COUNT_FILE="${SPEC_DIR}/mypy-count.txt"
REPORT_FILE="${SPEC_DIR}/mypy-report.txt"

# Ensure directories exist
mkdir -p "${SPEC_DIR}"

# Baseline (initial error count when SPEC was created)
BASELINE=1079

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MyPy Type Safety Progress Tracker${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Run MyPy
echo -e "${YELLOW}Running MyPy analysis...${NC}"
mypy apps/ tests/ --exclude '.venv|__pycache__|node_modules' 2>&1 | tee "${REPORT_FILE}"

# Extract error count
ERROR_LINE=$(grep "Found.*errors" "${REPORT_FILE}" || echo "Found 0 errors")
CURRENT_ERRORS=$(echo "${ERROR_LINE}" | grep -oP '\d+(?= error)' || echo "0")

# Calculate progress
FIXED_ERRORS=$((BASELINE - CURRENT_ERRORS))
PROGRESS_PCT=$((FIXED_ERRORS * 100 / BASELINE))

# Save to count file
echo "${ERROR_LINE}" > "${COUNT_FILE}"

# Append to history
{
    echo "============================================"
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "${ERROR_LINE}"
    echo "Progress: ${FIXED_ERRORS}/${BASELINE} errors fixed (${PROGRESS_PCT}%)"
    echo ""
} >> "${HISTORY_FILE}"

# Display summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Baseline:        ${BASELINE} errors"
echo -e "Current:         ${CURRENT_ERRORS} errors"
echo -e "Fixed:           ${GREEN}${FIXED_ERRORS}${NC} errors"
echo -e "Remaining:       ${RED}${CURRENT_ERRORS}${NC} errors"
echo -e "Progress:        ${GREEN}${PROGRESS_PCT}%${NC}"
echo ""

# Progress bar
BAR_WIDTH=40
FILLED=$((PROGRESS_PCT * BAR_WIDTH / 100))
EMPTY=$((BAR_WIDTH - FILLED))

printf "["
printf "%${FILLED}s" | tr ' ' '█'
printf "%${EMPTY}s" | tr ' ' '░'
printf "] ${PROGRESS_PCT}%%\n"
echo ""

# Top 10 files with most errors
echo -e "${YELLOW}Top 10 files with most errors:${NC}"
grep "^[^ ].*\.py:" "${REPORT_FILE}" | cut -d: -f1 | sort | uniq -c | sort -rn | head -10 | \
    awk '{printf "  %3d errors - %s\n", $1, $2}'
echo ""

# Error type distribution
echo -e "${YELLOW}Error type distribution (Top 10):${NC}"
grep "error:" "${REPORT_FILE}" | sed 's/.*error: //' | sed 's/\[.*\]//' | sort | uniq -c | sort -rn | head -10 | \
    awk '{count=$1; $1=""; printf "  %3d - %s\n", count, $0}'
echo ""

# Files saved
echo -e "${BLUE}Reports saved to:${NC}"
echo "  - Full report:  ${REPORT_FILE}"
echo "  - Error count:  ${COUNT_FILE}"
echo "  - History:      ${HISTORY_FILE}"
echo ""

# Verbose mode: show all errors
if [[ "${1:-}" == "--verbose" ]]; then
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  All Errors (Verbose Mode)${NC}"
    echo -e "${YELLOW}========================================${NC}"
    cat "${REPORT_FILE}"
fi

# Exit with MyPy's exit code
if [[ "${CURRENT_ERRORS}" -eq 0 ]]; then
    echo -e "${GREEN}🎉 Congratulations! All MyPy errors resolved!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  ${CURRENT_ERRORS} errors remaining. Keep going!${NC}"
    exit 1
fi
