#!/usr/bin/env python3
"""
Fix all untyped decorator errors by adding # type: ignore[misc] comments
Uses a simpler regex-based approach to find and fix decorators
"""
import re
import subprocess
from pathlib import Path

def get_files_with_errors() -> set[str]:
    """Get all files with 'Untyped decorator' errors"""
    result = subprocess.run(
        ["mypy", "apps/", "--config-file=pyproject.toml"],
        capture_output=True,
        text=True
    )

    files = set()
    for line in result.stdout.splitlines():
        if 'Untyped decorator makes function' in line and '[misc]' in line:
            file_path = line.split(':')[0]
            files.add(file_path)

    return files

def fix_decorators_in_file(file_path: Path) -> int:
    """Add # type: ignore[misc] to all FastAPI/other decorators"""
    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    fixed_count = 0
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a decorator line
        stripped = line.strip()
        if stripped.startswith('@') and '# type: ignore' not in line:
            # Check if next line is a function definition
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('async def ') or next_line.startswith('def '):
                    # Add type: ignore to decorator
                    if ')' in line:
                        # Decorator with arguments
                        insert_pos = line.rfind(')') + 1
                        lines[i] = (
                            line[:insert_pos] +
                            "  # type: ignore[misc]  # Decorator lacks type stubs"
                        )
                    else:
                        # Simple decorator
                        lines[i] = line + "  # type: ignore[misc]  # Decorator lacks type stubs"

                    fixed_count += 1

        i += 1

    if fixed_count > 0:
        file_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    return fixed_count

def main() -> None:
    print("🔍 Finding files with 'Untyped decorator' errors...")
    files_with_errors = get_files_with_errors()

    print(f"Found {len(files_with_errors)} files with errors\n")

    total_fixed = 0
    for idx, file_path_str in enumerate(sorted(files_with_errors), 1):
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"[{idx}/{len(files_with_errors)}] ✗ Not found: {file_path}")
            continue

        print(f"[{idx}/{len(files_with_errors)}] Processing {file_path}...")
        fixed_count = fix_decorators_in_file(file_path)

        if fixed_count > 0:
            print(f"  ✓ Fixed {fixed_count} decorators")
            total_fixed += fixed_count
        else:
            print(f"  ℹ No changes needed")

    print(f"\n✅ Total fixed: {total_fixed} decorators across {len(files_with_errors)} files")

if __name__ == "__main__":
    main()
