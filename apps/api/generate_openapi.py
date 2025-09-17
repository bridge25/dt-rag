#!/usr/bin/env python3
"""
OpenAPI Specification Generator for Dynamic Taxonomy RAG API v1.8.1

This script generates the OpenAPI specification files in JSON and YAML formats
for the Dynamic Taxonomy RAG system. It creates complete API documentation
including schemas, endpoints, authentication, and examples.

Usage:
    python generate_openapi.py [--output-dir OUTPUT_DIR] [--format json|yaml|both]
"""

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any

from openapi_spec import generate_openapi_spec


def save_json_spec(spec: Dict[str, Any], output_path: Path) -> None:
    """Save OpenAPI specification as JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False, default=str)

    print(f"✅ JSON specification saved to: {output_path}")


def save_yaml_spec(spec: Dict[str, Any], output_path: Path) -> None:
    """Save OpenAPI specification as YAML file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(spec, f, default_flow_style=False, allow_unicode=True,
                 sort_keys=False, indent=2)

    print(f"✅ YAML specification saved to: {output_path}")


def generate_spec_files(output_dir: str = ".", formats: str = "both") -> None:
    """Generate OpenAPI specification files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("🚀 Generating OpenAPI specification for Dynamic Taxonomy RAG API v1.8.1")
    print(f"📁 Output directory: {output_path.absolute()}")
    print(f"📋 Formats: {formats}")
    print()

    # Generate the OpenAPI specification
    try:
        spec = generate_openapi_spec()
        print("✅ OpenAPI specification generated successfully")
        print(f"📊 Generated {len(spec.get('paths', {}))} endpoint paths")
        print(f"📋 Generated {len(spec.get('components', {}).get('schemas', {}))} schemas")
        print()
    except Exception as e:
        print(f"❌ Failed to generate OpenAPI specification: {e}")
        return

    # Save in requested formats
    if formats in ["json", "both"]:
        json_path = output_path / "openapi.json"
        try:
            save_json_spec(spec, json_path)
        except Exception as e:
            print(f"❌ Failed to save JSON specification: {e}")

    if formats in ["yaml", "both"]:
        yaml_path = output_path / "openapi.yaml"
        try:
            save_yaml_spec(spec, yaml_path)
        except Exception as e:
            print(f"❌ Failed to save YAML specification: {e}")

    print()
    print("📖 Generated API documentation files:")

    if formats in ["json", "both"]:
        print(f"   📄 JSON: {output_path / 'openapi.json'}")

    if formats in ["yaml", "both"]:
        print(f"   📄 YAML: {output_path / 'openapi.yaml'}")

    print()
    print("🌐 To view the API documentation:")
    print("   1. Start the API server: python main.py")
    print("   2. Open Swagger UI: http://localhost:8000/docs")
    print("   3. Open ReDoc: http://localhost:8000/redoc")
    print("   4. Download spec: http://localhost:8000/api/v1/openapi.json")


def validate_spec(spec: Dict[str, Any]) -> None:
    """Validate the generated OpenAPI specification"""
    print("🔍 Validating OpenAPI specification...")

    # Check required fields
    required_fields = ["openapi", "info", "paths"]
    missing_fields = [field for field in required_fields if field not in spec]

    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return

    # Check OpenAPI version
    if not spec["openapi"].startswith("3.0"):
        print(f"⚠️  OpenAPI version {spec['openapi']} may not be fully supported")

    # Check info section
    info = spec.get("info", {})
    if not info.get("title"):
        print("❌ Missing API title in info section")

    if not info.get("version"):
        print("❌ Missing API version in info section")

    # Check paths
    paths = spec.get("paths", {})
    if not paths:
        print("❌ No API paths defined")

    # Count endpoints by method
    endpoint_count = {}
    for path, methods in paths.items():
        for method in methods:
            if method not in ["parameters", "summary", "description"]:
                endpoint_count[method.upper()] = endpoint_count.get(method.upper(), 0) + 1

    print("✅ OpenAPI specification validation completed")
    print(f"📊 Total endpoints: {sum(endpoint_count.values())}")
    for method, count in sorted(endpoint_count.items()):
        print(f"   {method}: {count} endpoints")

    # Check components
    components = spec.get("components", {})
    schemas = components.get("schemas", {})
    print(f"📋 Total schemas: {len(schemas)}")

    security_schemes = components.get("securitySchemes", {})
    print(f"🔒 Security schemes: {len(security_schemes)}")


def main():
    """Main function for CLI interface"""
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI specification for Dynamic Taxonomy RAG API"
    )

    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for generated files (default: current directory)"
    )

    parser.add_argument(
        "--format",
        choices=["json", "yaml", "both"],
        default="both",
        help="Output format for specification files (default: both)"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated specification"
    )

    args = parser.parse_args()

    # Generate specification files
    generate_spec_files(args.output_dir, args.format)

    # Validate if requested
    if args.validate:
        try:
            spec = generate_openapi_spec()
            validate_spec(spec)
        except Exception as e:
            print(f"❌ Validation failed: {e}")


if __name__ == "__main__":
    main()