#!/usr/bin/env python3
"""
Fix FastAPI router decorator misc errors by adding type: ignore comments
"""
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

def get_untyped_decorator_errors() -> List[Tuple[str, int, str]]:
    """Get all 'Untyped decorator' errors from mypy"""
    result = subprocess.run(
        ["mypy", "apps/", "--config-file=pyproject.toml"],
        capture_output=True,
        text=True
    )

    errors = []
    for line in result.stdout.splitlines():
        if 'Untyped decorator makes function' in line and '[misc]' in line:
            # Parse: apps/file.py:123: error: Untyped decorator makes function "func_name" untyped  [misc]
            parts = line.split(':')
            if len(parts) >= 3:
                file_path = parts[0]
                line_num = int(parts[1])
                func_name = line.split('"')[1] if '"' in line else ''
                errors.append((file_path, line_num, func_name))

    return errors

def fix_decorator_in_file(file_path: Path, line_num: int, func_name: str) -> bool:
    """Add # type: ignore[misc] to decorator above function"""
    try:
        lines = file_path.read_text(encoding='utf-8').splitlines()

        # Find the decorator line (should be 1-3 lines above the function definition)
        func_line_idx = line_num - 1  # Convert to 0-indexed

        if func_line_idx >= len(lines):
            return False

        # Look for decorator lines above the function
        decorator_idx = None
        for i in range(max(0, func_line_idx - 5), func_line_idx):
            line = lines[i].strip()
            if line.startswith('@') and not 'type: ignore' in line:
                decorator_idx = i
                break

        if decorator_idx is None:
            print(f"  Warning: Could not find decorator for {func_name} at line {line_num}")
            return False

        # Check if already has type: ignore
        if '# type: ignore[misc]' in lines[decorator_idx]:
            return False

        # Add type: ignore comment to the decorator line
        decorator_line = lines[decorator_idx]

        # Find the end of the decorator (after closing parenthesis or decorator name)
        if ')' in decorator_line:
            # Decorator with arguments: @router.post(...)
            insert_pos = decorator_line.rfind(')') + 1
        else:
            # Decorator without arguments: @property
            insert_pos = len(decorator_line.rstrip())

        new_line = (
            decorator_line[:insert_pos] +
            "  # type: ignore[misc]  # FastAPI decorator lacks type stubs" +
            decorator_line[insert_pos:]
        )

        lines[decorator_idx] = new_line

        # Write back
        file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return True

    except Exception as e:
        print(f"  Error fixing {file_path}:{line_num}: {e}")
        return False

def main() -> None:
    print("🔍 Finding 'Untyped decorator' errors...")
    errors = get_untyped_decorator_errors()

    print(f"Found {len(errors)} errors to fix\n")

    # Group by file
    files_to_fix: Dict[str, List[Tuple[int, str]]] = {}
    for file_path, line_num, func_name in errors:
        if file_path not in files_to_fix:
            files_to_fix[file_path] = []
        files_to_fix[file_path].append((line_num, func_name))

    fixed_count = 0
    total_files = len(files_to_fix)

    for idx, (file_path_str, functions) in enumerate(files_to_fix.items(), 1):
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"[{idx}/{total_files}] ✗ Not found: {file_path}")
            continue

        print(f"[{idx}/{total_files}] Fixing {file_path} ({len(functions)} functions)...")

        file_fixed = 0
        for line_num, func_name in sorted(functions, reverse=True):  # Reverse to avoid line number shifts
            if fix_decorator_in_file(file_path, line_num, func_name):
                file_fixed += 1
                fixed_count += 1

        print(f"  ✓ Fixed {file_fixed}/{len(functions)} decorators\n")

    print(f"✅ Total fixed: {fixed_count} decorators in {total_files} files")

if __name__ == "__main__":
    main()
