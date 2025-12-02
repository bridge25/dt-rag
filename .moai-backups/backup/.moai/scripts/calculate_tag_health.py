#!/usr/bin/env python3
"""
TAG Health Calculator
@CODE:TAG-CLEANUP-001

Calculates TAG Health score with multiple metrics and generates
graded health report.

Health Grade Scale:
    A+ (95-100%): Excellent - Production ready
    A  (90-94%):  Good - Minor issues
    B  (80-89%):  Fair - Needs attention
    C  (70-79%):  Poor - Significant issues
    D  (60-69%):  Critical - Major cleanup needed
    F  (0-59%):   Failing - Immediate action required

Usage:
    python calculate_tag_health.py
    python calculate_tag_health.py --scope production
    python calculate_tag_health.py --output health-report.json
"""

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import from other scripts
try:
    from scan_orphan_tags import TagScanner
    from validate_tag_chain import TagChainValidator
except ImportError:
    print("Error: Required modules not found. Ensure scan_orphan_tags.py and validate_tag_chain.py are in the same directory.", file=sys.stderr)
    sys.exit(1)


@dataclass
class HealthMetrics:
    """TAG Health metrics."""
    # Orphan metrics
    total_tags: int
    orphan_tags: int
    orphan_ratio: float  # 0-1

    # Chain integrity metrics
    total_specs: int
    complete_chains: int
    chain_integrity: float  # 0-100

    # Format compliance metrics
    format_violations: int
    format_compliance: float  # 0-100

    # Overall score
    overall_score: float  # 0-100
    health_grade: str  # A+, A, B, C, D, F

    # Scope-specific metrics
    scope: str  # production, all
    production_orphans: int = 0
    documentation_orphans: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class TagHealthCalculator:
    """Calculates TAG Health score."""

    # Weights for different metrics (must sum to 1.0)
    WEIGHTS = {
        'orphan_ratio': 0.40,      # 40% - Most critical
        'chain_integrity': 0.35,   # 35% - Very important
        'format_compliance': 0.25  # 25% - Important
    }

    # Grade thresholds
    GRADE_THRESHOLDS = {
        'A+': 95.0,
        'A': 90.0,
        'B': 80.0,
        'C': 70.0,
        'D': 60.0,
        'F': 0.0
    }

    def __init__(self, base_dir: Path, scope: str = 'all'):
        """
        Initialize TAG health calculator.

        Args:
            base_dir: Base directory to scan
            scope: 'production', 'documentation', or 'all'
        """
        self.base_dir = base_dir
        self.scope = scope

    def calculate_orphan_score(self, scanner: TagScanner) -> Dict[str, Union[int, float]]:
        """
        Calculate orphan ratio score.

        Lower orphan ratio = higher score.
        """
        report = scanner.generate_report()

        total_tags = report.total_tags
        orphan_tags = len(report.orphan_tags)

        # Calculate orphan ratio (0-1)
        orphan_ratio = 0.0
        if total_tags > 0:
            orphan_ratio = orphan_tags / total_tags

        # Convert to score (0-100, inverted)
        orphan_score = (1.0 - orphan_ratio) * 100.0

        return {
            'total_tags': total_tags,
            'orphan_tags': orphan_tags,
            'orphan_ratio': orphan_ratio,
            'orphan_score': orphan_score,
            'production_orphans': report.scope_breakdown.get('production', {}).get('orphans', 0),
            'documentation_orphans': report.scope_breakdown.get('documentation', {}).get('orphans', 0)
        }

    def calculate_chain_integrity_score(self, validator: TagChainValidator) -> Dict[str, Union[int, float]]:
        """
        Calculate chain integrity score.

        Higher chain integrity = higher score.
        """
        report = validator.generate_report()

        return {
            'total_specs': report.total_specs,
            'complete_chains': report.complete_chains,
            'chain_integrity': report.chain_integrity,
            'chain_score': report.chain_integrity  # Already 0-100
        }

    def calculate_format_compliance_score(self, validator: TagChainValidator) -> Dict[str, Union[int, float]]:
        """
        Calculate format compliance score.

        Fewer violations = higher score.
        """
        report = validator.generate_report()

        violations = len(report.format_violations)
        total_tags = report.total_specs * 3  # Assume avg 3 tags per spec

        # Calculate violation ratio
        violation_ratio = 0.0
        if total_tags > 0:
            violation_ratio = min(violations / total_tags, 1.0)

        # Convert to score (0-100, inverted)
        format_score = (1.0 - violation_ratio) * 100.0

        return {
            'format_violations': violations,
            'format_compliance': format_score,
            'format_score': format_score
        }

    def calculate_overall_score(
        self,
        orphan_score: float,
        chain_score: float,
        format_score: float
    ) -> float:
        """Calculate weighted overall health score."""
        overall = (
            orphan_score * self.WEIGHTS['orphan_ratio'] +
            chain_score * self.WEIGHTS['chain_integrity'] +
            format_score * self.WEIGHTS['format_compliance']
        )
        return overall

    def determine_grade(self, score: float) -> str:
        """Determine health grade based on score."""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return 'F'

    def calculate_health(self) -> HealthMetrics:
        """Calculate complete TAG health metrics."""
        print(f"Calculating TAG Health (scope: {self.scope})...")

        # Initialize scanners
        scanner = TagScanner(self.base_dir, self.scope)
        validator = TagChainValidator(self.base_dir)

        # Calculate individual scores
        print("  - Scanning orphan TAGs...")
        orphan_metrics = self.calculate_orphan_score(scanner)

        print("  - Validating TAG chains...")
        chain_metrics = self.calculate_chain_integrity_score(validator)

        print("  - Checking format compliance...")
        format_metrics = self.calculate_format_compliance_score(validator)

        # Calculate overall score
        overall_score = self.calculate_overall_score(
            orphan_metrics['orphan_score'],
            chain_metrics['chain_score'],
            format_metrics['format_score']
        )

        # Determine grade
        health_grade = self.determine_grade(overall_score)

        # Build metrics object
        metrics = HealthMetrics(
            total_tags=int(orphan_metrics['total_tags']),
            orphan_tags=int(orphan_metrics['orphan_tags']),
            orphan_ratio=float(orphan_metrics['orphan_ratio']),
            total_specs=int(chain_metrics['total_specs']),
            complete_chains=int(chain_metrics['complete_chains']),
            chain_integrity=float(chain_metrics['chain_integrity']),
            format_violations=int(format_metrics['format_violations']),
            format_compliance=float(format_metrics['format_compliance']),
            overall_score=overall_score,
            health_grade=health_grade,
            scope=self.scope,
            production_orphans=int(orphan_metrics['production_orphans']),
            documentation_orphans=int(orphan_metrics['documentation_orphans'])
        )

        return metrics


def print_health_report(metrics: HealthMetrics) -> None:
    """Print formatted health report."""
    print("\n" + "=" * 60)
    print("TAG HEALTH REPORT")
    print("=" * 60)

    # Overall grade
    print(f"\nOVERALL HEALTH GRADE: {metrics.health_grade} ({metrics.overall_score:.1f}%)")

    # Grade interpretation
    if metrics.health_grade in ['A+', 'A']:
        status = "✅ Excellent - Production ready"
    elif metrics.health_grade == 'B':
        status = "⚠️  Fair - Needs attention"
    elif metrics.health_grade == 'C':
        status = "❌ Poor - Significant issues"
    else:
        status = "🚨 Critical - Immediate action required"

    print(f"Status: {status}")

    # Detailed metrics
    print("\n" + "-" * 60)
    print("DETAILED METRICS")
    print("-" * 60)

    print(f"\n1. Orphan TAG Ratio: {metrics.orphan_ratio * 100:.1f}%")
    print(f"   Total TAGs: {metrics.total_tags}")
    print(f"   Orphan TAGs: {metrics.orphan_tags}")
    if metrics.scope == 'all':
        print(f"   - Production: {metrics.production_orphans}")
        print(f"   - Documentation: {metrics.documentation_orphans}")

    print(f"\n2. Chain Integrity: {metrics.chain_integrity:.1f}%")
    print(f"   Total SPECs: {metrics.total_specs}")
    print(f"   Complete Chains: {metrics.complete_chains}")
    print(f"   Incomplete Chains: {metrics.total_specs - metrics.complete_chains}")

    print(f"\n3. Format Compliance: {metrics.format_compliance:.1f}%")
    print(f"   Format Violations: {metrics.format_violations}")

    # Recommendations
    print("\n" + "-" * 60)
    print("RECOMMENDATIONS")
    print("-" * 60)

    if metrics.health_grade in ['A+', 'A']:
        print("✅ TAG system is healthy. Keep up the good work!")
    elif metrics.health_grade == 'B':
        print("⚠️  Consider:")
        if metrics.orphan_tags > 0:
            print("   - Clean up orphan TAGs")
        if metrics.chain_integrity < 90:
            print("   - Complete incomplete TAG chains")
        if metrics.format_violations > 0:
            print("   - Fix format violations")
    else:
        print("❌ Priority actions:")
        if metrics.production_orphans > 0:
            print(f"   1. Remove {metrics.production_orphans} production orphan TAGs (CRITICAL)")
        if metrics.orphan_tags > 0:
            print(f"   2. Clean up {metrics.orphan_tags} total orphan TAGs")
        if metrics.chain_integrity < 70:
            print("   3. Improve TAG chain integrity")
        if metrics.format_violations > 10:
            print(f"   4. Fix {metrics.format_violations} format violations")

    print("\n" + "=" * 60)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate TAG Health score'
    )
    parser.add_argument(
        '--scope',
        choices=['production', 'documentation', 'all'],
        default='all',
        help='Scope to calculate (default: all)'
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

    # Calculate health
    calculator = TagHealthCalculator(args.base_dir, args.scope)
    metrics = calculator.calculate_health()

    # Print report
    print_health_report(metrics)

    # Save to JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)

        print(f"\nReport saved to: {output_path}")

    # Exit with appropriate code
    if metrics.health_grade in ['D', 'F']:
        sys.exit(1)
    elif metrics.health_grade == 'C':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
