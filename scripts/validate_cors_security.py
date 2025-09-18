#!/usr/bin/env python3
"""
CORS Security Validation Script
Validates that all CORS configurations in the DT-RAG system are secure.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class CORSSecurityValidator:
    """Validates CORS configurations for security vulnerabilities"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.vulnerabilities = []
        self.files_checked = []

    def validate_all(self) -> bool:
        """
        Validate all CORS configurations in the project

        Returns:
            bool: True if all configurations are secure, False otherwise
        """
        print("🔍 Scanning for CORS configurations...")

        # Find all Python files with CORS configuration
        cors_files = self._find_cors_files()

        print(f"📁 Found {len(cors_files)} files with CORS configuration")

        # Validate each file
        for file_path in cors_files:
            self._validate_file(file_path)

        # Print results
        self._print_results()

        return len(self.vulnerabilities) == 0

    def _find_cors_files(self) -> List[Path]:
        """Find all Python files containing CORS middleware configuration"""
        cors_files = []

        # Search pattern for CORS-related code
        cors_patterns = [
            r'CORSMiddleware',
            r'allow_origins\s*=',
            r'allow_headers\s*=',
            r'allow_methods\s*='
        ]

        # Search in apps directory
        apps_dir = self.project_root / "apps"
        if apps_dir.exists():
            for py_file in apps_dir.rglob("*.py"):
                try:
                    content = py_file.read_text(encoding='utf-8')
                    if any(re.search(pattern, content) for pattern in cors_patterns):
                        cors_files.append(py_file)
                        self.files_checked.append(str(py_file))
                except Exception as e:
                    print(f"⚠️  Warning: Could not read {py_file}: {e}")

        return cors_files

    def _validate_file(self, file_path: Path) -> None:
        """Validate CORS configuration in a single file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            print(f"\n📄 Validating {file_path.relative_to(self.project_root)}")

            # Check for wildcard vulnerabilities
            self._check_wildcard_origins(file_path, content, lines)
            self._check_wildcard_headers(file_path, content, lines)
            self._check_wildcard_methods(file_path, content, lines)
            self._check_credentials_with_wildcards(file_path, content, lines)

        except Exception as e:
            print(f"❌ Error validating {file_path}: {e}")

    def _check_wildcard_origins(self, file_path: Path, content: str, lines: List[str]) -> None:
        """Check for wildcard origins"""
        wildcard_patterns = [
            r'allow_origins\s*=\s*\[.*"\*".*\]',
            r'allow_origins\s*=\s*"\*"',
            r'allow_origins.*\*'
        ]

        for i, line in enumerate(lines):
            for pattern in wildcard_patterns:
                if re.search(pattern, line):
                    self.vulnerabilities.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': i + 1,
                        'type': 'WILDCARD_ORIGINS',
                        'severity': 'CRITICAL',
                        'content': line.strip(),
                        'description': 'Wildcard origins allow any domain to make requests'
                    })

    def _check_wildcard_headers(self, file_path: Path, content: str, lines: List[str]) -> None:
        """Check for wildcard headers"""
        wildcard_patterns = [
            r'allow_headers\s*=\s*\[.*"\*".*\]',
            r'allow_headers\s*=\s*"\*"',
            r'allow_headers.*\*'
        ]

        for i, line in enumerate(lines):
            for pattern in wildcard_patterns:
                if re.search(pattern, line):
                    self.vulnerabilities.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': i + 1,
                        'type': 'WILDCARD_HEADERS',
                        'severity': 'HIGH',
                        'content': line.strip(),
                        'description': 'Wildcard headers allow any header to be sent'
                    })

    def _check_wildcard_methods(self, file_path: Path, content: str, lines: List[str]) -> None:
        """Check for wildcard methods"""
        wildcard_patterns = [
            r'allow_methods\s*=\s*\[.*"\*".*\]',
            r'allow_methods\s*=\s*"\*"',
            r'allow_methods.*\*'
        ]

        for i, line in enumerate(lines):
            for pattern in wildcard_patterns:
                if re.search(pattern, line):
                    self.vulnerabilities.append({
                        'file': str(file_path.relative_to(self.project_root)),
                        'line': i + 1,
                        'type': 'WILDCARD_METHODS',
                        'severity': 'HIGH',
                        'content': line.strip(),
                        'description': 'Wildcard methods allow any HTTP method'
                    })

    def _check_credentials_with_wildcards(self, file_path: Path, content: str, lines: List[str]) -> None:
        """Check for credentials enabled with wildcard origins"""
        # Look for allow_credentials=True with wildcard origins in the same middleware block
        cors_blocks = self._extract_cors_blocks(content)

        for block_start, block_content in cors_blocks:
            has_credentials = 'allow_credentials=True' in block_content or 'allow_credentials = True' in block_content
            has_wildcard_origins = '"*"' in block_content and 'allow_origins' in block_content

            if has_credentials and has_wildcard_origins:
                self.vulnerabilities.append({
                    'file': str(file_path.relative_to(self.project_root)),
                    'line': block_start,
                    'type': 'CREDENTIALS_WITH_WILDCARD',
                    'severity': 'CRITICAL',
                    'content': 'CORS credentials enabled with wildcard origins',
                    'description': 'Credentials should not be enabled with wildcard origins'
                })

    def _extract_cors_blocks(self, content: str) -> List[Tuple[int, str]]:
        """Extract CORS middleware configuration blocks"""
        lines = content.split('\n')
        cors_blocks = []

        in_cors_block = False
        block_start = 0
        block_lines = []

        for i, line in enumerate(lines):
            if 'CORSMiddleware' in line:
                in_cors_block = True
                block_start = i + 1
                block_lines = [line]
            elif in_cors_block:
                block_lines.append(line)
                # Check if we've reached the end of the middleware block
                if line.strip() == ')' or (line.strip().endswith(')') and 'add_middleware' not in line):
                    cors_blocks.append((block_start, '\n'.join(block_lines)))
                    in_cors_block = False
                    block_lines = []

        return cors_blocks

    def _print_results(self) -> None:
        """Print validation results"""
        print("\n" + "="*60)
        print("🔒 CORS Security Validation Results")
        print("="*60)

        if not self.vulnerabilities:
            print("✅ All CORS configurations are secure!")
            print(f"📊 Checked {len(self.files_checked)} files")
            return

        # Group vulnerabilities by severity
        critical = [v for v in self.vulnerabilities if v['severity'] == 'CRITICAL']
        high = [v for v in self.vulnerabilities if v['severity'] == 'HIGH']
        medium = [v for v in self.vulnerabilities if v['severity'] == 'MEDIUM']

        if critical:
            print(f"\n🔴 CRITICAL VULNERABILITIES ({len(critical)}):")
            for vuln in critical:
                print(f"   📁 {vuln['file']}:{vuln['line']}")
                print(f"   🔍 {vuln['type']}: {vuln['description']}")
                print(f"   📝 {vuln['content']}")
                print()

        if high:
            print(f"\n🟠 HIGH RISK VULNERABILITIES ({len(high)}):")
            for vuln in high:
                print(f"   📁 {vuln['file']}:{vuln['line']}")
                print(f"   🔍 {vuln['type']}: {vuln['description']}")
                print(f"   📝 {vuln['content']}")
                print()

        if medium:
            print(f"\n🟡 MEDIUM RISK VULNERABILITIES ({len(medium)}):")
            for vuln in medium:
                print(f"   📁 {vuln['file']}:{vuln['line']}")
                print(f"   🔍 {vuln['type']}: {vuln['description']}")
                print(f"   📝 {vuln['content']}")
                print()

        print(f"\n📊 Summary:")
        print(f"   🔴 Critical: {len(critical)}")
        print(f"   🟠 High: {len(high)}")
        print(f"   🟡 Medium: {len(medium)}")
        print(f"   📁 Files checked: {len(self.files_checked)}")
        print(f"   ❌ Total vulnerabilities: {len(self.vulnerabilities)}")


def main():
    """Main entry point"""
    # Get project root (assuming script is in scripts/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print("🔐 CORS Security Validation Tool")
    print("="*40)
    print(f"📂 Project root: {project_root}")

    # Validate CORS configurations
    validator = CORSSecurityValidator(str(project_root))
    is_secure = validator.validate_all()

    # Exit with appropriate code
    if is_secure:
        print("\n✅ All CORS configurations are secure for production deployment!")
        sys.exit(0)
    else:
        print("\n❌ CORS security vulnerabilities found. Please fix before deploying to production.")
        sys.exit(1)


if __name__ == "__main__":
    main()