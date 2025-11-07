#!/usr/bin/env python3
"""
TAG Chain Validator
@CODE:TAG-CLEANUP-001

Validates the integrity of TAG chains (@SPEC → @CODE → @TEST → @DOC)
and checks for broken references and format violations.

Usage:
    python validate_tag_chain.py
    python validate_tag_chain.py --spec-id AUTH-001
    python validate_tag_chain.py --output validation-report.json
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Set, Optional


@dataclass
class TagChainNode:
    """Single node in TAG chain."""
    tag_type: str  # SPEC, CODE, TEST, DOC
    tag_id: str
    file_path: str
    line_number: int
    exists: bool = True


@dataclass
class TagChain:
    """Complete TAG chain for a SPEC."""
    spec_id: str
    spec_node: Optional[TagChainNode] = None
    code_nodes: List[TagChainNode] = field(default_factory=list)
    test_nodes: List[TagChainNode] = field(default_factory=list)
    doc_nodes: List[TagChainNode] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Check if chain has all required components."""
        return (
            self.spec_node is not None
            and len(self.code_nodes) > 0
            and len(self.test_nodes) > 0
        )

    @property
    def completeness_ratio(self) -> float:
        """Calculate chain completeness (0-1)."""
        components = 0
        if self.spec_node:
            components += 1
        if self.code_nodes:
            components += 1
        if self.test_nodes:
            components += 1
        if self.doc_nodes:
            components += 1
        return components / 4.0


@dataclass
class ValidationReport:
    """TAG chain validation report."""
    total_specs: int = 0
    complete_chains: int = 0
    incomplete_chains: int = 0
    chain_integrity: float = 0.0
    broken_chains: List[Dict[str, str]] = field(default_factory=list)
    format_violations: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class TagChainValidator:
    """Validates TAG chain integrity."""

    # TAG patterns (strict format)
    TAG_PATTERNS = {
        'SPEC': re.compile(r'@SPEC:([A-Z][A-Z0-9-]+-\d{3})'),
        'CODE': re.compile(r'@CODE:([A-Z][A-Z0-9-]+-\d{3})'),
        'TEST': re.compile(r'@TEST:([A-Z][A-Z0-9-]+-\d{3})'),
        'DOC': re.compile(r'@DOC:([A-Z][A-Z0-9-]+-\d{3})'),
    }

    # Invalid TAG patterns (format violations)
    INVALID_PATTERNS = [
        r'@CODE:ID\b',           # Placeholder
        r'@TEST:0\b',            # Invalid ID
        r'@TEST:ID\b',           # Placeholder
        r'@CODE:EXISTING\b',     # Legacy
        r'@[A-Z]+:[a-z]',        # Lowercase in ID
        r'@[A-Z]+:\d{1,2}\b',    # Too short
    ]

    def __init__(self, base_dir: Path):
        """
        Initialize TAG chain validator.

        Args:
            base_dir: Base directory to scan
        """
        self.base_dir = base_dir
        self.chains: Dict[str, TagChain] = {}

    def _run_ripgrep(self, pattern: str, directory: Optional[str] = None) -> List[str]:
        """Run ripgrep (or grep fallback) and return output lines."""
        search_dir = str(self.base_dir / directory) if directory else str(self.base_dir)
        # Convert \d to [0-9] for grep compatibility
        grep_pattern = pattern.replace(r'\d', '[0-9]')

        try:
            # Try ripgrep first
            result = subprocess.run(
                ['rg', pattern, '-n', '--no-heading', search_dir],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout.splitlines()

        except FileNotFoundError:
            # Fallback to grep
            try:
                result = subprocess.run(
                    ['grep', '-rEn', grep_pattern, search_dir],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return result.stdout.splitlines()

            except FileNotFoundError:
                print("Error: Neither 'rg' (ripgrep) nor 'grep' found.", file=sys.stderr)
                sys.exit(1)

    def scan_tag_type(self, tag_type: str) -> List[TagChainNode]:
        """
        Scan for specific TAG type.

        Args:
            tag_type: Type of TAG to scan (SPEC, CODE, TEST, DOC)

        Returns:
            List of TagChainNode objects
        """
        pattern = self.TAG_PATTERNS[tag_type]
        nodes: List[TagChainNode] = []

        lines = self._run_ripgrep(pattern.pattern)

        for line in lines:
            # Parse rg output: filename:line_number:line_content
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue

            file_path = parts[0]
            line_number = int(parts[1])
            line_content = parts[2].strip()

            # Extract TAG ID
            match = pattern.search(line_content)
            if match:
                tag_id = match.group(1)
                nodes.append(TagChainNode(
                    tag_type=tag_type,
                    tag_id=tag_id,
                    file_path=file_path,
                    line_number=line_number
                ))

        return nodes

    def build_chains(self) -> None:
        """Build TAG chains from scanned nodes."""
        # Scan all TAG types
        spec_nodes = self.scan_tag_type('SPEC')
        code_nodes = self.scan_tag_type('CODE')
        test_nodes = self.scan_tag_type('TEST')
        doc_nodes = self.scan_tag_type('DOC')

        # Create chains keyed by SPEC ID
        for spec in spec_nodes:
            if spec.tag_id not in self.chains:
                self.chains[spec.tag_id] = TagChain(spec_id=spec.tag_id)
            # Only set if from official specs directory
            if '.moai/specs/' in spec.file_path:
                self.chains[spec.tag_id].spec_node = spec

        # Add CODE nodes
        for code in code_nodes:
            if code.tag_id not in self.chains:
                self.chains[code.tag_id] = TagChain(spec_id=code.tag_id)
            self.chains[code.tag_id].code_nodes.append(code)

        # Add TEST nodes
        for test in test_nodes:
            if test.tag_id not in self.chains:
                self.chains[test.tag_id] = TagChain(spec_id=test.tag_id)
            self.chains[test.tag_id].test_nodes.append(test)

        # Add DOC nodes
        for doc in doc_nodes:
            if doc.tag_id not in self.chains:
                self.chains[doc.tag_id] = TagChain(spec_id=doc.tag_id)
            self.chains[doc.tag_id].doc_nodes.append(doc)

    def check_format_violations(self) -> List[Dict[str, str]]:
        """Check for TAG format violations."""
        violations: List[Dict[str, str]] = []

        for pattern in self.INVALID_PATTERNS:
            lines = self._run_ripgrep(pattern)

            for line in lines:
                parts = line.split(':', 2)
                if len(parts) < 3:
                    continue

                file_path = parts[0]
                line_number = int(parts[1])
                line_content = parts[2].strip()

                violations.append({
                    'file_path': file_path,
                    'line_number': str(line_number),
                    'line_content': line_content,
                    'violation': pattern,
                    'reason': 'Invalid TAG format'
                })

        return violations

    def identify_broken_chains(self) -> List[Dict[str, str]]:
        """Identify broken TAG chains."""
        broken: List[Dict[str, str]] = []

        for spec_id, chain in self.chains.items():
            issues: List[str] = []

            # Missing SPEC definition
            if chain.spec_node is None:
                issues.append('Missing @SPEC definition')

            # Missing CODE implementation
            if not chain.code_nodes:
                issues.append('Missing @CODE implementation')

            # Missing TEST coverage
            if not chain.test_nodes:
                issues.append('Missing @TEST coverage')

            # Report broken chains
            if issues:
                broken.append({
                    'spec_id': spec_id,
                    'issues': ', '.join(issues),
                    'completeness': f"{chain.completeness_ratio * 100:.1f}%",
                    'has_spec': 'yes' if chain.spec_node else 'no',
                    'code_count': str(len(chain.code_nodes)),
                    'test_count': str(len(chain.test_nodes)),
                    'doc_count': str(len(chain.doc_nodes))
                })

        return broken

    def generate_report(self) -> ValidationReport:
        """Generate validation report."""
        # Build chains
        self.build_chains()

        # Calculate integrity
        complete_chains = sum(1 for chain in self.chains.values() if chain.is_complete)
        total_specs = len(self.chains)

        chain_integrity = 0.0
        if total_specs > 0:
            chain_integrity = (complete_chains / total_specs) * 100.0

        # Identify broken chains
        broken_chains = self.identify_broken_chains()

        # Check format violations
        format_violations = self.check_format_violations()

        # Build report
        report = ValidationReport(
            total_specs=total_specs,
            complete_chains=complete_chains,
            incomplete_chains=total_specs - complete_chains,
            chain_integrity=chain_integrity,
            broken_chains=broken_chains,
            format_violations=format_violations
        )

        return report


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate TAG chain integrity'
    )
    parser.add_argument(
        '--spec-id',
        type=str,
        default=None,
        help='Validate specific SPEC ID only'
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

    # Initialize validator
    validator = TagChainValidator(args.base_dir)

    # Generate report
    print("Validating TAG chains...")
    report = validator.generate_report()

    # Display summary
    print("\n=== TAG Chain Validation Report ===")
    print(f"Total SPECs: {report.total_specs}")
    print(f"Complete Chains: {report.complete_chains}")
    print(f"Incomplete Chains: {report.incomplete_chains}")
    print(f"Chain Integrity: {report.chain_integrity:.1f}%")

    print(f"\n=== Issues ===")
    print(f"Broken Chains: {len(report.broken_chains)}")
    print(f"Format Violations: {len(report.format_violations)}")

    # Show broken chains (limit to first 10)
    if report.broken_chains:
        print("\n=== Sample Broken Chains (first 10) ===")
        for broken in report.broken_chains[:10]:
            print(f"\nSPEC: {broken['spec_id']}")
            print(f"  Issues: {broken['issues']}")
            print(f"  Completeness: {broken['completeness']}")

    # Show format violations (limit to first 10)
    if report.format_violations:
        print("\n=== Sample Format Violations (first 10) ===")
        for violation in report.format_violations[:10]:
            print(f"\n{violation['file_path']}:{violation['line_number']}")
            print(f"  Violation: {violation['violation']}")
            print(f"  Content: {violation['line_content'][:80]}")

    # Save to JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)

        print(f"\nReport saved to: {output_path}")

    # Exit with error code if integrity < 100%
    if report.chain_integrity < 100.0:
        print("\n⚠️  WARNING: TAG chain integrity is below 100%", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
