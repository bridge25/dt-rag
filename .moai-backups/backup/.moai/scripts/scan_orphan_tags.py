#!/usr/bin/env python3
"""
TAG Orphan Scanner
@CODE:TAG-CLEANUP-001

Scans directories for @TAG annotations and identifies orphan TAGs
(TAGs without matching @SPEC references).

Usage:
    python scan_orphan_tags.py --scope production
    python scan_orphan_tags.py --scope all
    python scan_orphan_tags.py --output report.json
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class TagInfo:
    """Information about a single TAG occurrence."""
    tag_type: str  # SPEC, CODE, TEST, DOC
    tag_id: str  # e.g., AUTH-001
    file_path: str
    line_number: int
    line_content: str
    scope: str  # production or documentation


@dataclass
class ScanReport:
    """Complete TAG scan report."""
    total_tags: int = 0
    spec_tags: int = 0
    code_tags: int = 0
    test_tags: int = 0
    doc_tags: int = 0
    orphan_tags: List[Dict[str, str]] = field(default_factory=list)
    scope_breakdown: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class TagScanner:
    """Scans codebase for TAG annotations."""

    # TAG patterns (flexible to match domain-NNN or DOMAIN-SUB-NNN formats)
    SPEC_PATTERN = re.compile(r'@SPEC:([A-Z][A-Z0-9-]+-\d{3})')
    CODE_PATTERN = re.compile(r'@CODE:([A-Z][A-Z0-9-]+-\d{3})')
    TEST_PATTERN = re.compile(r'@TEST:([A-Z][A-Z0-9-]+-\d{3})')
    DOC_PATTERN = re.compile(r'@DOC:([A-Z][A-Z0-9-]+-\d{3})')

    # Directory classifications
    PRODUCTION_DIRS = ['apps/', 'tests/']
    DOCUMENTATION_DIRS = ['.moai/', '.claude/', 'moai/', 'docs/', '.git/']

    # Documentation subdirectories inside production dirs
    DOC_SUBDIRS = ['.claude/', '.moai/', 'docs/', 'moai/']

    def __init__(self, base_dir: Path, scope: str = 'all'):
        """
        Initialize TAG scanner.

        Args:
            base_dir: Base directory to scan
            scope: 'production', 'documentation', or 'all'
        """
        self.base_dir = base_dir
        self.scope = scope
        self.spec_ids: Set[str] = set()
        self.all_tags: List[TagInfo] = []

    def scan_specs(self) -> None:
        """Scan .moai/specs/ directory for valid @SPEC IDs."""
        specs_dir = self.base_dir / '.moai' / 'specs'
        if not specs_dir.exists():
            print(f"Warning: SPEC directory not found: {specs_dir}", file=sys.stderr)
            return

        try:
            # Try ripgrep first
            result = subprocess.run(
                ['rg', r'@SPEC:[A-Z][A-Z0-9-]+-\d{3}', '-o', '--no-filename', str(specs_dir)],
                capture_output=True,
                text=True,
                check=False
            )

            for line in result.stdout.splitlines():
                match = self.SPEC_PATTERN.search(line)
                if match:
                    self.spec_ids.add(match.group(1))

        except FileNotFoundError:
            # Fallback to grep
            try:
                result = subprocess.run(
                    ['grep', '-rEho', r'@SPEC:[A-Z][A-Z0-9-]+-[0-9]{3}', str(specs_dir)],
                    capture_output=True,
                    text=True,
                    check=False
                )

                for line in result.stdout.splitlines():
                    match = self.SPEC_PATTERN.search(line)
                    if match:
                        self.spec_ids.add(match.group(1))

            except FileNotFoundError:
                print("Error: Neither 'rg' (ripgrep) nor 'grep' found.", file=sys.stderr)
                sys.exit(1)

    def _get_scope_for_path(self, file_path: str) -> str:
        """Determine if file is in production or documentation scope."""
        # Normalize path to relative if absolute
        if file_path.startswith(str(self.base_dir)):
            file_path = str(Path(file_path).relative_to(self.base_dir))
        # Remove leading './' if present (from grep/rg relative paths)
        elif file_path.startswith('./'):
            file_path = file_path[2:]

        # Check for documentation subdirectories first
        for doc_subdir in self.DOC_SUBDIRS:
            if f'/{doc_subdir}' in file_path or file_path.startswith(doc_subdir):
                return 'documentation'

        # Then check for production directories
        for prod_dir in self.PRODUCTION_DIRS:
            if file_path.startswith(prod_dir):
                return 'production'

        # Finally check for top-level documentation directories
        for doc_dir in self.DOCUMENTATION_DIRS:
            if file_path.startswith(doc_dir):
                return 'documentation'

        return 'other'

    def _should_scan_path(self, file_path: str) -> bool:
        """Check if file path should be scanned based on scope setting."""
        scope = self._get_scope_for_path(file_path)

        if self.scope == 'all':
            return True
        elif self.scope == 'production':
            return scope == 'production'
        elif self.scope == 'documentation':
            return scope == 'documentation'

        return False

    def scan_tags(self, pattern: re.Pattern, tag_type: str) -> List[TagInfo]:
        """
        Scan for specific TAG pattern.

        Args:
            pattern: Regex pattern to match
            tag_type: Type of TAG (SPEC, CODE, TEST, DOC)

        Returns:
            List of TagInfo objects
        """
        tags: List[TagInfo] = []

        try:
            # Try ripgrep first
            result = subprocess.run(
                ['rg', pattern.pattern, '-n', '--no-heading', str(self.base_dir)],
                capture_output=True,
                text=True,
                check=False
            )

            for line in result.stdout.splitlines():
                # Parse rg output: filename:line_number:line_content
                parts = line.split(':', 2)
                if len(parts) < 3:
                    continue

                file_path = parts[0]
                line_number = int(parts[1])
                line_content = parts[2].strip()

                # Check scope filter
                if not self._should_scan_path(file_path):
                    continue

                # Extract TAG ID
                match = pattern.search(line_content)
                if match:
                    tag_id = match.group(1)
                    scope = self._get_scope_for_path(file_path)

                    tags.append(TagInfo(
                        tag_type=tag_type,
                        tag_id=tag_id,
                        file_path=file_path,
                        line_number=line_number,
                        line_content=line_content,
                        scope=scope
                    ))

        except FileNotFoundError:
            # Fallback to grep (convert Python regex \d to grep [0-9])
            try:
                grep_pattern = pattern.pattern.replace(r'\d', '[0-9]')
                result = subprocess.run(
                    ['grep', '-rEn', grep_pattern, str(self.base_dir)],
                    capture_output=True,
                    text=True,
                    check=False
                )

                for line in result.stdout.splitlines():
                    # Parse grep output: filename:line_number:line_content
                    parts = line.split(':', 2)
                    if len(parts) < 3:
                        continue

                    file_path = parts[0]
                    line_number = int(parts[1])
                    line_content = parts[2].strip()

                    # Check scope filter
                    if not self._should_scan_path(file_path):
                        continue

                    # Extract TAG ID
                    match = pattern.search(line_content)
                    if match:
                        tag_id = match.group(1)
                        scope = self._get_scope_for_path(file_path)

                        tags.append(TagInfo(
                            tag_type=tag_type,
                            tag_id=tag_id,
                            file_path=file_path,
                            line_number=line_number,
                            line_content=line_content,
                            scope=scope
                        ))

            except FileNotFoundError:
                print("Error: Neither 'rg' (ripgrep) nor 'grep' found.", file=sys.stderr)
                sys.exit(1)

        return tags

    def identify_orphans(self) -> List[TagInfo]:
        """Identify TAGs without matching @SPEC."""
        orphans: List[TagInfo] = []

        for tag in self.all_tags:
            # Skip @SPEC tags themselves
            if tag.tag_type == 'SPEC':
                continue

            # Check if corresponding SPEC exists
            if tag.tag_id not in self.spec_ids:
                orphans.append(tag)

        return orphans

    def generate_report(self) -> ScanReport:
        """Generate comprehensive scan report."""
        # Scan for all SPEC IDs first
        self.scan_specs()

        # Scan for all TAG types
        self.all_tags.extend(self.scan_tags(self.SPEC_PATTERN, 'SPEC'))
        self.all_tags.extend(self.scan_tags(self.CODE_PATTERN, 'CODE'))
        self.all_tags.extend(self.scan_tags(self.TEST_PATTERN, 'TEST'))
        self.all_tags.extend(self.scan_tags(self.DOC_PATTERN, 'DOC'))

        # Identify orphans
        orphans = self.identify_orphans()

        # Calculate scope breakdown
        scope_breakdown: Dict[str, Dict[str, int]] = {
            'production': {'total': 0, 'orphans': 0},
            'documentation': {'total': 0, 'orphans': 0},
            'other': {'total': 0, 'orphans': 0}
        }

        for tag in self.all_tags:
            if tag.scope in scope_breakdown:
                scope_breakdown[tag.scope]['total'] += 1

        for orphan in orphans:
            if orphan.scope in scope_breakdown:
                scope_breakdown[orphan.scope]['orphans'] += 1

        # Build report
        report = ScanReport(
            total_tags=len(self.all_tags),
            spec_tags=sum(1 for t in self.all_tags if t.tag_type == 'SPEC'),
            code_tags=sum(1 for t in self.all_tags if t.tag_type == 'CODE'),
            test_tags=sum(1 for t in self.all_tags if t.tag_type == 'TEST'),
            doc_tags=sum(1 for t in self.all_tags if t.tag_type == 'DOC'),
            orphan_tags=[
                {
                    'tag_type': o.tag_type,
                    'tag_id': o.tag_id,
                    'file_path': o.file_path,
                    'line_number': str(o.line_number),
                    'scope': o.scope
                }
                for o in orphans
            ],
            scope_breakdown=scope_breakdown
        )

        return report


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Scan codebase for orphan @TAG annotations'
    )
    parser.add_argument(
        '--scope',
        choices=['production', 'documentation', 'all'],
        default='all',
        help='Scope to scan (default: all)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output JSON file path'
    )
    parser.add_argument(
        '--base-dir',
        type=Path,
        default=Path.cwd(),
        help='Base directory to scan (default: current directory)'
    )

    args = parser.parse_args()

    # Initialize scanner
    scanner = TagScanner(args.base_dir, args.scope)

    # Generate report
    print(f"Scanning TAGs in scope: {args.scope}...")
    report = scanner.generate_report()

    # Display summary
    print("\n=== TAG Scan Report ===")
    print(f"Total TAGs: {report.total_tags}")
    print(f"  @SPEC: {report.spec_tags}")
    print(f"  @CODE: {report.code_tags}")
    print(f"  @TEST: {report.test_tags}")
    print(f"  @DOC: {report.doc_tags}")
    print(f"\nOrphan TAGs: {len(report.orphan_tags)}")

    print("\n=== Scope Breakdown ===")
    for scope, stats in report.scope_breakdown.items():
        print(f"{scope.capitalize()}:")
        print(f"  Total: {stats['total']}")
        print(f"  Orphans: {stats['orphans']}")

    # Save to JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        print(f"\nReport saved to: {output_path}")

    # Exit with error code if orphans found in production
    if args.scope == 'production' and report.scope_breakdown['production']['orphans'] > 0:
        print("\n⚠️  WARNING: Orphan TAGs found in production code!", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
