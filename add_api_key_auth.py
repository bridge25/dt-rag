"""
Add API Key authentication to all routers that don't have it
"""
import re
from pathlib import Path

routers_to_update = [
    "apps/api/routers/classification_router.py",
    "apps/api/routers/taxonomy_router.py",
    "apps/api/routers/orchestration_router.py",
    "apps/api/routers/agent_factory_router.py"
]

def add_api_key_to_endpoint(content: str, decorator_pattern: str) -> tuple[str, int]:
    """Add api_key parameter to endpoints"""
    changes = 0

    # Pattern: @router.method("/path")
    # followed by async def function_name(
    # We need to add api_key: str = Depends(verify_api_key) parameter

    pattern = r'(@\w+_router\.(get|post|put|delete|patch)\([^)]+\)[^\n]*\n)(async def \w+\([^)]*)'

    def replacer(match):
        nonlocal changes
        decorator = match.group(1)
        func_sig_start = match.group(3)

        # Check if already has verify_api_key
        if 'verify_api_key' in func_sig_start or 'api_key' in func_sig_start:
            return match.group(0)  # Already has auth

        # Add api_key parameter
        if func_sig_start.endswith('('):
            # No parameters yet
            new_sig = func_sig_start + '\n    api_key: str = Depends(verify_api_key)'
        else:
            # Has parameters, add after last one
            new_sig = func_sig_start + ',\n    api_key: str = Depends(verify_api_key)'

        changes += 1
        return decorator + new_sig

    new_content = re.sub(pattern, replacer, content)
    return new_content, changes

def process_router(file_path: str):
    """Process a single router file"""
    path = Path(file_path)

    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    print(f"\n📝 Processing: {file_path}")

    content = path.read_text(encoding='utf-8')

    # Check if deps import exists
    if 'from ..deps import verify_api_key' not in content and 'verify_api_key' not in content:
        print("  ➕ Adding deps import...")
        # Find import section
        import_pattern = r'(from fastapi import[^\n]+\n)'
        import_add = r'\1\n# Import API key authentication\ntry:\n    from ..deps import verify_api_key\nexcept ImportError:\n    def verify_api_key():\n        return None\n'
        content = re.sub(import_pattern, import_add, content, count=1)

    # Add api_key to endpoints
    new_content, changes = add_api_key_to_endpoint(content, file_path)

    if changes > 0:
        path.write_text(new_content, encoding='utf-8')
        print(f"  ✅ Added API key auth to {changes} endpoints")
        return True
    else:
        print(f"  ℹ️  No changes needed (all endpoints already have auth or no endpoints found)")
        return False

def main():
    """Main entry point"""
    print("=" * 70)
    print("Adding API Key Authentication to Routers")
    print("=" * 70)

    total_updated = 0

    for router_file in routers_to_update:
        if process_router(router_file):
            total_updated += 1

    print("\n" + "=" * 70)
    print(f"✅ Updated {total_updated}/{len(routers_to_update)} routers")
    print("=" * 70)

if __name__ == "__main__":
    main()
