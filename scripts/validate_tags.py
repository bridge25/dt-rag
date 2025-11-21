#!/usr/bin/env python3
"""
TAG Validation Script for dt-rag-standalone

Scans codebase for @SPEC, @CODE, @TEST, @DOC tags and validates chain integrity.
Outputs JSON report and markdown comment for CI/CD integration.

Usage:
    python scripts/validate_tags.py [--strict] [--output-json FILE] [--output-md FILE]

@CODE:CI-001
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class TagInfo:
    """Information about a single TAG occurrence"""

    tag_type: str  # SPEC, CODE, TEST, DOC
    domain: str  # e.g., SEARCH, API, DATABASE
    number: str  # e.g., 001
    file_path: str
    line_number: int

    @property
    def full_tag(self) -> str:
        return f"@{self.tag_type}:{self.domain}-{self.number}"

    @property
    def domain_id(self) -> str:
        return f"{self.domain}-{self.number}"


@dataclass
class ValidationResult:
    """Result of TAG validation"""

    is_valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    tags_by_type: dict = field(default_factory=lambda: defaultdict(list))
    tags_by_domain: dict = field(default_factory=lambda: defaultdict(list))
    orphan_code_tags: list = field(default_factory=list)  # CODE without TEST
    orphan_test_tags: list = field(default_factory=list)  # TEST without CODE
    statistics: dict = field(default_factory=dict)


# TAG regex pattern: @(SPEC|CODE|TEST|DOC):DOMAIN-NNN
TAG_PATTERN = re.compile(r"@(SPEC|CODE|TEST|DOC):([A-Z][A-Z0-9-]*)-(\d{3})")

# File extensions to scan
PYTHON_EXTENSIONS = {".py"}
TYPESCRIPT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}
DOCUMENTATION_EXTENSIONS = {".md"}
ALL_EXTENSIONS = PYTHON_EXTENSIONS | TYPESCRIPT_EXTENSIONS | DOCUMENTATION_EXTENSIONS

# Directories to exclude
EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".next",
    "coverage",
    ".moai",
}


def should_skip_dir(dir_name: str) -> bool:
    """Check if directory should be skipped"""
    return dir_name in EXCLUDE_DIRS or dir_name.startswith(".")


def scan_file_for_tags(file_path: Path) -> list[TagInfo]:
    """Scan a single file for TAG annotations"""
    tags = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.split("\n"), start=1):
            for match in TAG_PATTERN.finditer(line):
                tag_type, domain, number = match.groups()
                tags.append(
                    TagInfo(
                        tag_type=tag_type,
                        domain=domain,
                        number=number,
                        file_path=str(file_path),
                        line_number=line_num,
                    )
                )
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    return tags


def scan_directory(root_path: Path) -> list[TagInfo]:
    """Recursively scan directory for TAG annotations"""
    all_tags = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d)]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if file_path.suffix in ALL_EXTENSIONS:
                all_tags.extend(scan_file_for_tags(file_path))

    return all_tags


def validate_tags(tags: list[TagInfo], strict: bool = False) -> ValidationResult:
    """Validate TAG chain integrity"""
    result = ValidationResult()

    # Organize tags by type and domain
    for tag in tags:
        result.tags_by_type[tag.tag_type].append(tag)
        result.tags_by_domain[tag.domain_id].append(tag)

    # Build domain sets for each type
    code_domains = {t.domain_id for t in result.tags_by_type.get("CODE", [])}
    test_domains = {t.domain_id for t in result.tags_by_type.get("TEST", [])}
    spec_domains = {t.domain_id for t in result.tags_by_type.get("SPEC", [])}

    # Find orphan CODE tags (CODE without corresponding TEST)
    for code_tag in result.tags_by_type.get("CODE", []):
        if code_tag.domain_id not in test_domains:
            result.orphan_code_tags.append(code_tag)
            if strict:
                result.errors.append(
                    f"Orphan @CODE tag: {code_tag.full_tag} in {code_tag.file_path}:{code_tag.line_number} has no corresponding @TEST"
                )
                result.is_valid = False
            else:
                result.warnings.append(
                    f"@CODE tag {code_tag.full_tag} in {code_tag.file_path} has no corresponding @TEST"
                )

    # Find orphan TEST tags (TEST without corresponding CODE)
    for test_tag in result.tags_by_type.get("TEST", []):
        if test_tag.domain_id not in code_domains:
            result.orphan_test_tags.append(test_tag)
            result.warnings.append(
                f"@TEST tag {test_tag.full_tag} in {test_tag.file_path} has no corresponding @CODE"
            )

    # Calculate statistics
    result.statistics = {
        "total_tags": len(tags),
        "spec_tags": len(result.tags_by_type.get("SPEC", [])),
        "code_tags": len(result.tags_by_type.get("CODE", [])),
        "test_tags": len(result.tags_by_type.get("TEST", [])),
        "doc_tags": len(result.tags_by_type.get("DOC", [])),
        "unique_domains": len(result.tags_by_domain),
        "orphan_code_count": len(result.orphan_code_tags),
        "orphan_test_count": len(result.orphan_test_tags),
        "total_errors": len(result.errors),
        "total_warnings": len(result.warnings),
        "code_coverage": (
            len(code_domains & test_domains) / len(code_domains) * 100
            if code_domains
            else 100.0
        ),
    }

    return result


def generate_json_report(result: ValidationResult, output_path: Optional[str] = None) -> str:
    """Generate JSON report"""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_valid": result.is_valid,
        "status": "success" if result.is_valid else "failure",
        "statistics": result.statistics,
        "errors": result.errors,
        "warnings": result.warnings[:20],  # Limit warnings in report
        "tags_summary": {
            tag_type: len(tags) for tag_type, tags in result.tags_by_type.items()
        },
        "domains": list(result.tags_by_domain.keys()),
    }

    json_str = json.dumps(report, indent=2)

    if output_path:
        Path(output_path).write_text(json_str)
        print(f"JSON report written to {output_path}")

    return json_str


def generate_markdown_report(result: ValidationResult, output_path: Optional[str] = None) -> str:
    """Generate Markdown report for PR comment"""
    stats = result.statistics

    if result.is_valid:
        status_emoji = "✅"
        status_text = "Passed"
    else:
        status_emoji = "❌"
        status_text = "Failed"

    md = f"""## {status_emoji} TAG Validation {status_text}

### Statistics

| Metric | Count |
|--------|-------|
| Total TAGs | {stats['total_tags']} |
| @SPEC | {stats['spec_tags']} |
| @CODE | {stats['code_tags']} |
| @TEST | {stats['test_tags']} |
| @DOC | {stats['doc_tags']} |
| Unique Domains | {stats['unique_domains']} |
| CODE Coverage | {stats['code_coverage']:.1f}% |

### Validation Results

- **Errors**: {stats['total_errors']}
- **Warnings**: {stats['total_warnings']}
- **Orphan @CODE (no @TEST)**: {stats['orphan_code_count']}
- **Orphan @TEST (no @CODE)**: {stats['orphan_test_count']}
"""

    if result.errors:
        md += "\n### Errors\n\n"
        for error in result.errors[:10]:
            md += f"- {error}\n"
        if len(result.errors) > 10:
            md += f"\n... and {len(result.errors) - 10} more errors\n"

    if result.warnings:
        md += "\n### Warnings\n\n"
        md += "<details>\n<summary>Click to expand warnings</summary>\n\n"
        for warning in result.warnings[:20]:
            md += f"- {warning}\n"
        if len(result.warnings) > 20:
            md += f"\n... and {len(result.warnings) - 20} more warnings\n"
        md += "\n</details>\n"

    md += f"\n---\n\n*Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*\n"

    if output_path:
        Path(output_path).write_text(md)
        print(f"Markdown report written to {output_path}")

    return md


def main():
    parser = argparse.ArgumentParser(description="Validate TAG annotations in codebase")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: fail on orphan CODE tags",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output JSON report to file",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        help="Output Markdown report to file",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Root path to scan (default: current directory)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )

    args = parser.parse_args()

    root_path = Path(args.path).resolve()

    if not args.quiet:
        print(f"Scanning {root_path} for TAG annotations...")

    # Scan for tags
    tags = scan_directory(root_path)

    if not args.quiet:
        print(f"Found {len(tags)} TAG annotations")

    # Validate
    result = validate_tags(tags, strict=args.strict)

    # Generate reports
    if args.output_json:
        generate_json_report(result, args.output_json)

    if args.output_md:
        generate_markdown_report(result, args.output_md)

    # Print summary
    if not args.quiet:
        print("\n" + "=" * 50)
        print("TAG Validation Summary")
        print("=" * 50)
        print(f"Total TAGs: {result.statistics['total_tags']}")
        print(f"  @SPEC: {result.statistics['spec_tags']}")
        print(f"  @CODE: {result.statistics['code_tags']}")
        print(f"  @TEST: {result.statistics['test_tags']}")
        print(f"  @DOC: {result.statistics['doc_tags']}")
        print(f"Unique Domains: {result.statistics['unique_domains']}")
        print(f"CODE Coverage: {result.statistics['code_coverage']:.1f}%")
        print(f"Orphan @CODE: {result.statistics['orphan_code_count']}")
        print(f"Orphan @TEST: {result.statistics['orphan_test_count']}")
        print(f"Errors: {result.statistics['total_errors']}")
        print(f"Warnings: {result.statistics['total_warnings']}")
        print("=" * 50)
        print(f"Status: {'PASSED' if result.is_valid else 'FAILED'}")

    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
