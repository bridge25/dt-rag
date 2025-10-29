#!/usr/bin/env python3
"""
Fix @observe decorator misc errors by adding type: ignore comments
"""
import re
import sys
from pathlib import Path

def fix_observe_decorators(file_path: Path) -> bool:
    """Add # type: ignore[misc] to @observe decorators that lack it"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # Pattern: @observe(...) without already having # type: ignore[misc]
    # Look for @observe decorators that don't already have the comment
    pattern = r'(@observe\([^)]+\))(?!\s*#\s*type:\s*ignore\[misc\])'
    replacement = r'\1  # type: ignore[misc]  # Langfuse decorator lacks type stubs'

    content = re.sub(pattern, replacement, content)

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        return True
    return False

def main() -> None:
    # Get all Python files with @observe decorators that have misc errors
    files_with_errors = [
        "apps/api/embedding_service.py",
        "apps/evaluation/evaluation_router.py",
        "apps/evaluation/dashboard.py",
    ]

    fixed_count = 0
    for file_path_str in files_with_errors:
        file_path = Path(file_path_str)
        if file_path.exists():
            if fix_observe_decorators(file_path):
                print(f"✓ Fixed: {file_path}")
                fixed_count += 1
        else:
            print(f"✗ Not found: {file_path}")

    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()
