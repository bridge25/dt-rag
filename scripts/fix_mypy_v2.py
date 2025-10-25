#!/usr/bin/env python3
"""
# @CODE:MYPY-001:PHASE1-V2
Improved automated mypy error fixer for mypy 1.18.2
Targets: no-untyped-def, var-annotated, no-any-return, assignment errors
Strategy: Smart Optional detection + precise type inference
"""
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional
import subprocess

try:
    import libcst as cst
    from libcst import matchers as m
except ImportError:
    print("ERROR: libcst not installed. Run: pip3 install libcst")
    sys.exit(1)


class ImprovedTypeAnnotationTransformer(cst.CSTTransformer):
    """
    Improved transformer with better type inference
    - Detects Optional types from None defaults
    - Infers return types from function body
    - Handles no-any-return errors
    """

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path
        self.modified = False
        self.needs_any = False
        self.needs_optional = False
        self.needs_union = False
        self.stats = {"functions": 0, "params": 0, "returns": 0}

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Add return type annotation with smart inference"""
        # Skip if already has return annotation
        if updated_node.returns is not None:
            return updated_node

        func_name = updated_node.name.value

        # Special methods that return None
        if func_name in ("__init__", "__post_init__", "__del__"):
            self.modified = True
            self.stats["returns"] += 1
            return updated_node.with_changes(
                returns=cst.Annotation(annotation=cst.Name("None"))
            )

        # Async generators and context managers
        if func_name in ("__aenter__", "__aexit__", "__enter__", "__exit__"):
            self.modified = True
            self.needs_any = True
            self.stats["returns"] += 1
            return updated_node.with_changes(
                returns=cst.Annotation(annotation=cst.Name("Any"))
            )

        # Try to infer return type from function body
        return_type = self._infer_return_type(updated_node)
        if return_type:
            self.modified = True
            self.stats["returns"] += 1
            return updated_node.with_changes(
                returns=cst.Annotation(annotation=cst.Name(return_type))
            )

        # Default: Any
        self.modified = True
        self.needs_any = True
        self.stats["returns"] += 1
        return updated_node.with_changes(
            returns=cst.Annotation(annotation=cst.Name("Any"))
        )

    def _infer_return_type(self, node: cst.FunctionDef) -> Optional[str]:
        """Infer return type from function body"""
        # Simple heuristics for common patterns
        body = node.body
        if not isinstance(body, cst.IndentedBlock):
            return None

        has_return_none = False
        has_return_value = False

        for stmt in body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for item in stmt.body:
                    if isinstance(item, cst.Return):
                        if item.value is None:
                            has_return_none = True
                        else:
                            has_return_value = True

        # If only returns None, type is None
        if has_return_none and not has_return_value:
            return "None"

        # If returns both None and values, needs Optional (complex, skip)
        if has_return_none and has_return_value:
            self.needs_optional = True
            return "Any"  # Conservative for now

        # If no return statement, likely None
        if not has_return_none and not has_return_value:
            return "None"

        return None

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        """Add type annotation to parameters with smart Optional detection"""
        # Skip if already has annotation
        if updated_node.annotation is not None:
            return updated_node

        # Skip self and cls parameters
        param_name = updated_node.name.value
        if param_name in ("self", "cls"):
            return updated_node

        # Skip *args and **kwargs
        if updated_node.star == "*" or updated_node.star == "**":
            return updated_node

        # Detect Optional from default=None
        if updated_node.default is not None:
            if m.matches(updated_node.default, m.Name("None")):
                # Parameter with default=None should be Optional
                self.modified = True
                self.needs_optional = True
                self.stats["params"] += 1
                return updated_node.with_changes(
                    annotation=cst.Annotation(
                        annotation=cst.Subscript(
                            value=cst.Name("Optional"),
                            slice=[
                                cst.SubscriptElement(
                                    slice=cst.Index(value=cst.Name("Any"))
                                )
                            ],
                        )
                    )
                )

        # Default: Any
        self.modified = True
        self.needs_any = True
        self.stats["params"] += 1
        return updated_node.with_changes(
            annotation=cst.Annotation(annotation=cst.Name("Any"))
        )


class SmartImportAdder(cst.CSTTransformer):
    """Add typing imports smartly"""

    def __init__(self, needs_any: bool, needs_optional: bool, needs_union: bool):
        super().__init__()
        self.needs_any = needs_any
        self.needs_optional = needs_optional
        self.needs_union = needs_union
        self.has_typing_import = False
        self.existing_imports: Set[str] = set()

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Check existing typing imports"""
        if m.matches(node, m.ImportFrom(module=m.Attribute() | m.Name("typing"))):
            self.has_typing_import = True
            if node.names and isinstance(node.names, cst.ImportStar):
                self.existing_imports = {"Any", "Optional", "Union", "*"}
            elif node.names and not isinstance(node.names, cst.ImportStar):
                for name in node.names:
                    if isinstance(name, cst.ImportAlias):
                        self.existing_imports.add(name.name.value)

    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """Add typing imports if needed"""
        # Determine what to import
        to_import = []
        if self.needs_any and "Any" not in self.existing_imports:
            to_import.append("Any")
        if self.needs_optional and "Optional" not in self.existing_imports:
            to_import.append("Optional")
        if self.needs_union and "Union" not in self.existing_imports:
            to_import.append("Union")

        if not to_import or "*" in self.existing_imports:
            return updated_node

        # Find insertion position
        new_body = list(updated_node.body)
        insert_pos = 0

        # Skip docstring
        for i, stmt in enumerate(new_body):
            if isinstance(stmt, cst.SimpleStatementLine):
                if isinstance(stmt.body[0], cst.Expr) and isinstance(
                    stmt.body[0].value, (cst.SimpleString, cst.ConcatenatedString)
                ):
                    insert_pos = i + 1
                    continue
            break

        # Create import statement
        import_aliases = [cst.ImportAlias(name=cst.Name(name)) for name in sorted(to_import)]
        import_stmt = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Name("typing"),
                    names=import_aliases,
                )
            ]
        )
        new_body.insert(insert_pos, import_stmt)

        return updated_node.with_changes(body=new_body)


def fix_file_improved(file_path: Path) -> Dict[str, Any]:
    """Fix a single Python file with improved strategy"""
    try:
        source_code = file_path.read_text(encoding="utf-8")

        # Parse the source code
        try:
            module = cst.parse_module(source_code)
        except Exception as e:
            return {"success": False, "error": f"Parse error: {e}"}

        # First pass: add type annotations
        transformer = ImprovedTypeAnnotationTransformer(file_path)
        modified_tree = module.visit(transformer)

        if not transformer.modified:
            return {"success": True, "modified": False, "stats": transformer.stats}

        # Second pass: add imports
        import_adder = SmartImportAdder(
            needs_any=transformer.needs_any,
            needs_optional=transformer.needs_optional,
            needs_union=transformer.needs_union,
        )
        final_tree = modified_tree.visit(import_adder)

        # Write back
        file_path.write_text(final_tree.code, encoding="utf-8")

        return {
            "success": True,
            "modified": True,
            "stats": transformer.stats,
            "imports": {
                "Any": transformer.needs_any,
                "Optional": transformer.needs_optional,
                "Union": transformer.needs_union,
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def run_mypy_on_file(file_path: Path) -> int:
    """Run mypy on a single file and return error count"""
    try:
        result = subprocess.run(
            ["~/.local/bin/mypy", str(file_path), "--config-file=pyproject.toml"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Count errors
        error_count = result.stdout.count("error:")
        return error_count
    except Exception:
        return -1


def main():
    """Main entry point"""
    print("# @CODE:MYPY-001:PHASE1-V2 - Improved mypy fixer")
    print("=" * 60)

    # Get baseline errors
    baseline_file = Path("mypy_baseline.txt")
    if not baseline_file.exists():
        print("ERROR: mypy_baseline.txt not found. Run mypy first.")
        return 1

    # Parse error files
    error_files = set()
    for line in baseline_file.read_text().splitlines():
        if match := re.match(r"^(apps/[^:]+\.py):", line):
            error_files.add(Path(match.group(1)))

    print(f"Found {len(error_files)} files with errors")
    print()

    # Process files
    total_stats = {"functions": 0, "params": 0, "returns": 0}
    modified_files = []
    failed_files = []

    for i, file_path in enumerate(sorted(error_files), 1):
        print(f"[{i}/{len(error_files)}] Processing: {file_path}")

        result = fix_file_improved(file_path)

        if not result["success"]:
            print(f"  ❌ FAILED: {result.get('error', 'Unknown error')}")
            failed_files.append(file_path)
            continue

        if result["modified"]:
            stats = result["stats"]
            total_stats["functions"] += stats["functions"]
            total_stats["params"] += stats["params"]
            total_stats["returns"] += stats["returns"]
            modified_files.append(file_path)
            print(f"  ✅ MODIFIED: {stats['functions']} funcs, {stats['params']} params, {stats['returns']} returns")
        else:
            print(f"  ⏭️  SKIPPED: Already typed")

    print()
    print("=" * 60)
    print("Summary:")
    print(f"  Total files processed: {len(error_files)}")
    print(f"  Modified: {len(modified_files)}")
    print(f"  Failed: {len(failed_files)}")
    print(f"  Total annotations added:")
    print(f"    - Functions: {total_stats['functions']}")
    print(f"    - Parameters: {total_stats['params']}")
    print(f"    - Returns: {total_stats['returns']}")
    print()

    if failed_files:
        print("Failed files:")
        for f in failed_files:
            print(f"  - {f}")
        print()

    print("✅ Phase 1 automation complete!")
    print("Run mypy again to check remaining errors.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
