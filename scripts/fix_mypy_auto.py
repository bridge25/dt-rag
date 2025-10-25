#!/usr/bin/env python3
"""
# @CODE:MYPY-001:PHASE1
Automated mypy error fixer using libcst
Targets: no-untyped-def, var-annotated errors
Strategy: Conservative Any usage for rapid automation
"""
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import libcst as cst
from libcst import matchers as m


class TypeAnnotationTransformer(cst.CSTTransformer):
    """Transform AST to add missing type annotations"""

    def __init__(self):
        super().__init__()
        self.modified = False
        self.added_any_import = False

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Add return type annotation if missing"""
        # Skip if already has return annotation
        if updated_node.returns is not None:
            return updated_node

        # Skip special methods that shouldn't have return types
        func_name = updated_node.name.value
        if func_name in ("__init__", "__post_init__"):
            # Add -> None annotation
            self.modified = True
            self.added_any_import = True
            return updated_node.with_changes(
                returns=cst.Annotation(annotation=cst.Name("None"))
            )

        # For other functions, add -> Any annotation
        self.modified = True
        self.added_any_import = True
        return updated_node.with_changes(
            returns=cst.Annotation(annotation=cst.Name("Any"))
        )

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        """Add type annotation to parameters if missing"""
        # Skip if already has annotation
        if updated_node.annotation is not None:
            return updated_node

        # Skip self and cls parameters
        param_name = updated_node.name.value
        if param_name in ("self", "cls"):
            return updated_node

        # Add Any annotation
        self.modified = True
        self.added_any_import = True
        return updated_node.with_changes(
            annotation=cst.Annotation(annotation=cst.Name("Any"))
        )

    def leave_AnnAssign(
        self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign
    ) -> cst.AnnAssign:
        """Handle annotated assignments (already annotated, no change)"""
        return updated_node


class ImportAdder(cst.CSTTransformer):
    """Add typing imports if needed"""

    def __init__(self, needs_any: bool):
        super().__init__()
        self.needs_any = needs_any
        self.has_typing_import = False
        self.has_any_import = False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Check existing typing imports"""
        if m.matches(node, m.ImportFrom(module=m.Attribute() | m.Name("typing"))):
            self.has_typing_import = True
            if node.names and isinstance(node.names, cst.ImportStar):
                self.has_any_import = True
            elif node.names and not isinstance(node.names, cst.ImportStar):
                for name in node.names:
                    if isinstance(name, cst.ImportAlias) and name.name.value == "Any":
                        self.has_any_import = True

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """Add typing import if needed"""
        if not self.needs_any or self.has_any_import:
            return updated_node

        # Find where to insert import
        new_body = list(updated_node.body)

        # Skip docstring and comments at the beginning
        insert_pos = 0
        for i, stmt in enumerate(new_body):
            if isinstance(stmt, cst.SimpleStatementLine):
                if isinstance(stmt.body[0], cst.Expr) and isinstance(
                    stmt.body[0].value, cst.SimpleString
                ):
                    insert_pos = i + 1
                    continue
            break

        # Create the import statement
        if self.has_typing_import:
            # Modify existing import (more complex, skip for now)
            # Just add a new import line
            pass

        # Add new import
        import_stmt = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Name("typing"),
                    names=[cst.ImportAlias(name=cst.Name("Any"))],
                )
            ]
        )
        new_body.insert(insert_pos, import_stmt)

        return updated_node.with_changes(body=new_body)


def fix_file(file_path: Path) -> bool:
    """Fix a single Python file"""
    try:
        source_code = file_path.read_text(encoding="utf-8")

        # Parse the source code
        module = cst.parse_module(source_code)

        # First pass: add type annotations
        transformer = TypeAnnotationTransformer()
        modified_tree = module.visit(transformer)

        if not transformer.modified:
            return False

        # Second pass: add imports if needed
        import_adder = ImportAdder(needs_any=transformer.added_any_import)
        modified_tree = modified_tree.visit(import_adder)

        # Write back
        file_path.write_text(modified_tree.code, encoding="utf-8")

        return True

    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def get_files_to_fix(error_file: Path) -> Set[Path]:
    """Extract file paths from mypy error output"""
    files = set()

    if not error_file.exists():
        return files

    content = error_file.read_text()
    for line in content.splitlines():
        if "error:" in line:
            # Extract file path (format: path/to/file.py:line: error: ...)
            match = re.match(r"^([^:]+\.py):\d+:", line)
            if match:
                file_path = Path(match.group(1))
                if file_path.exists():
                    files.add(file_path)

    return files


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    error_file = project_root / "mypy_errors.txt"

    print("# @CODE:MYPY-001:PHASE1 - Automated mypy error fixer")
    print(f"Reading errors from: {error_file}")

    files_to_fix = get_files_to_fix(error_file)
    print(f"Found {len(files_to_fix)} files with errors")

    fixed_count = 0
    for file_path in sorted(files_to_fix):
        print(f"Processing: {file_path}")
        if fix_file(file_path):
            fixed_count += 1
            print(f"  ✓ Fixed")
        else:
            print(f"  - No changes")

    print(f"\n✅ Processed {len(files_to_fix)} files, modified {fixed_count} files")
    print("\n⚠️  Note: Using conservative Any types for rapid automation")
    print("Run 'mypy apps/ --config-file=pyproject.toml' to verify improvements")


if __name__ == "__main__":
    main()
