#!/usr/bin/env python3
"""
Import Validator - Pre-commit Hook
@CODE:CICD-001:HOOK | SPEC: SPEC-CICD-001.md | Phase 2

Validates Python imports before git commit to catch errors early.
Integrated with MoAI-ADK Alfred hook system.

HISTORY:
v0.0.1 (2025-01-24): INITIAL - Pre-commit import validation
"""

import sys
import subprocess
from pathlib import Path
from typing import Tuple, List


def run_command(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    """Run shell command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 60 seconds"
    except Exception as e:
        return 1, "", str(e)


def validate_python_syntax(project_root: Path) -> Tuple[bool, str]:
    """Validate Python syntax using compileall"""
    print("🔍 Stage 1: Python 구문 검증 중...")

    # Check if Python directories exist
    apps_dir = project_root / "apps"
    tests_dir = project_root / "tests"

    dirs_to_check = []
    if apps_dir.exists():
        dirs_to_check.append("apps/")
    if tests_dir.exists():
        dirs_to_check.append("tests/")

    if not dirs_to_check:
        return True, "✓ No Python directories to check"

    cmd = ["python3", "-m", "compileall", "-q"] + dirs_to_check
    exit_code, stdout, stderr = run_command(cmd, project_root)

    if exit_code == 0:
        print("✓ Python 구문 검증 통과")
        return True, "✓ Python syntax validation passed"
    else:
        return False, f"✗ Python syntax errors found:\n{stderr}"


def validate_api_imports(project_root: Path) -> Tuple[bool, str]:
    """Validate API imports"""
    print("🔍 API import 검증 중...")

    main_py = project_root / "apps" / "api" / "main.py"
    if not main_py.exists():
        return True, "✓ No API to check"

    # Use python to import the module
    cmd = [
        "python3", "-c",
        "from apps.api.main import app; print('✓ API imports validated')"
    ]

    exit_code, stdout, stderr = run_command(cmd, project_root)

    if exit_code == 0:
        print("✓ API import 검증 통과")
        return True, "✓ API imports validated"
    else:
        # Extract useful error message
        error_lines = stderr.strip().split('\n')
        # Get last few lines which usually contain the actual error
        relevant_error = '\n'.join(error_lines[-5:])
        return False, f"✗ API import errors found:\n{relevant_error}"


def main() -> int:
    """Main validation function"""
    print("=" * 60)
    print("🛡️ MoAI-ADK Pre-commit Import Validation (Phase 2)")
    print("=" * 60)

    # Get project root (dt-rag directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent  # .claude/hooks/alfred -> dt-rag

    print(f"📁 Project root: {project_root}")
    print()

    # API import validation (includes syntax validation)
    import_ok, import_msg = validate_api_imports(project_root)

    print()
    print("=" * 60)

    if import_ok:
        print("✅ Import 검증 통과 - 커밋을 진행합니다")
        print("=" * 60)
        return 0
    else:
        print(f"❌ {import_msg}")
        print()
        print("❌ Import 검증 실패 - 커밋이 차단되었습니다")
        print()
        print("💡 문제를 수정한 후 다시 커밋하세요:")
        print("   1. 위의 오류 메시지를 확인하세요")
        print("   2. Import 오류를 수정하세요")
        print("   3. git commit을 다시 실행하세요")
        print()
        print("⚠️  검증을 건너뛰려면 (권장하지 않음):")
        print("   git commit --no-verify")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
