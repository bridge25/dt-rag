#!/bin/bash
# Security Scanning Script
# @CODE:TEST-004-006:SCAN | SPEC: SPEC-TEST-004.md

set -e

echo "=================================="
echo "Security Scanning for dt-rag"
echo "=================================="
echo ""

# Create reports directory if it doesn't exist
mkdir -p security_reports

# 1. Bandit - Python security linter
echo "[1/2] Running Bandit (Python Security Linter)..."
echo "Command: bandit -r apps/ -f txt -o security_reports/bandit_report.txt"

if command -v bandit &> /dev/null; then
    bandit -r apps/ -f txt -o security_reports/bandit_report.txt || true
    echo "✅ Bandit scan complete"
    echo "Report: security_reports/bandit_report.txt"

    # Show summary
    echo ""
    echo "Bandit Summary:"
    tail -15 security_reports/bandit_report.txt
else
    echo "⚠️  Bandit not installed. Install with: pip install bandit>=1.7.5"
    echo "Skipping bandit scan."
fi

echo ""
echo "=================================="

# 2. Safety - Dependency vulnerability scanner
echo "[2/2] Running Safety (Dependency Scanner)..."
echo "Command: safety check --json"

if command -v safety &> /dev/null; then
    safety check --json > security_reports/safety_report.json 2>&1 || true
    echo "✅ Safety scan complete"
    echo "Report: security_reports/safety_report.json"

    # Show summary
    echo ""
    echo "Safety Summary:"
    if [ -f security_reports/safety_report.json ]; then
        cat security_reports/safety_report.json | head -20
    fi
else
    echo "⚠️  Safety not installed. Install with: pip install safety>=3.0.0"
    echo "Skipping safety scan."
fi

echo ""
echo "=================================="
echo "Security scan completed!"
echo "Reports saved in: security_reports/"
echo "=================================="
