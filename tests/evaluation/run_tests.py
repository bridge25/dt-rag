#!/usr/bin/env python3
"""
Test runner for RAG evaluation framework
Provides easy commands to run different test suites
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print("Make sure pytest is installed: pip install pytest")
        return False


def run_unit_tests():
    """Run fast unit tests"""
    cmd = [
        "python", "-m", "pytest",
        "-m", "not integration and not performance and not slow",
        "--tb=short",
        "-v"
    ]
    return run_command(cmd, "Unit Tests")


def run_integration_tests():
    """Run integration tests"""
    cmd = [
        "python", "-m", "pytest",
        "-m", "integration",
        "--tb=short",
        "-v"
    ]
    return run_command(cmd, "Integration Tests")


def run_performance_tests():
    """Run performance tests"""
    cmd = [
        "python", "-m", "pytest",
        "-m", "performance",
        "--tb=short",
        "-v",
        "--runslow"
    ]
    return run_command(cmd, "Performance Tests")


def run_all_tests():
    """Run all tests including slow ones"""
    cmd = [
        "python", "-m", "pytest",
        "--tb=short",
        "-v",
        "--runslow",
        "--runintegration"
    ]
    return run_command(cmd, "All Tests")


def run_coverage_report():
    """Run tests with coverage report"""
    cmd = [
        "python", "-m", "pytest",
        "--cov=core",
        "--cov=orchestrator",
        "--cov=api",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml",
        "-v"
    ]
    return run_command(cmd, "Tests with Coverage")


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "--tb=short",
        "-v"
    ]
    return run_command(cmd, f"Specific Test: {test_path}")


def run_lint_checks():
    """Run code quality checks"""
    print("\n" + "="*60)
    print("Running Code Quality Checks")
    print("="*60)

    success = True

    # Check if flake8 is available
    try:
        cmd = ["python", "-m", "flake8", "../../apps/evaluation/", "--max-line-length=100"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Flake8 checks passed")
        else:
            print("❌ Flake8 checks failed:")
            print(result.stdout)
            success = False
    except FileNotFoundError:
        print("⚠️  Flake8 not found (optional)")

    # Check if black is available
    try:
        cmd = ["python", "-m", "black", "--check", "../../apps/evaluation/"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Black formatting checks passed")
        else:
            print("❌ Black formatting checks failed")
            print("Run: python -m black ../../apps/evaluation/")
            success = False
    except FileNotFoundError:
        print("⚠️  Black not found (optional)")

    return success


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n" + "="*60)
    print("Checking Dependencies")
    print("="*60)

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "ragas",
        "datasets",
        "langchain",
        "fastapi",
        "scipy",
        "scikit-learn",
        "pandas",
        "numpy"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    else:
        print("\n✅ All dependencies are installed")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for RAG evaluation framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py unit                    # Run unit tests only
  python run_tests.py integration            # Run integration tests
  python run_tests.py performance            # Run performance tests
  python run_tests.py all                    # Run all tests
  python run_tests.py coverage               # Run with coverage report
  python run_tests.py lint                   # Run code quality checks
  python run_tests.py deps                   # Check dependencies
  python run_tests.py specific test_ragas_engine.py  # Run specific test
        """
    )

    parser.add_argument(
        "command",
        choices=["unit", "integration", "performance", "all", "coverage", "lint", "deps", "specific"],
        help="Test command to run"
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Specific test file or function (for 'specific' command)"
    )

    args = parser.parse_args()

    # Change to test directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    print(f"🚀 RAG Evaluation Framework Test Runner")
    print(f"Working directory: {os.getcwd()}")

    success = True

    if args.command == "unit":
        success = run_unit_tests()
    elif args.command == "integration":
        success = run_integration_tests()
    elif args.command == "performance":
        success = run_performance_tests()
    elif args.command == "all":
        success = run_all_tests()
    elif args.command == "coverage":
        success = run_coverage_report()
    elif args.command == "lint":
        success = run_lint_checks()
    elif args.command == "deps":
        success = check_dependencies()
    elif args.command == "specific":
        if not args.target:
            print("❌ Specific test target is required")
            print("Example: python run_tests.py specific test_ragas_engine.py")
            sys.exit(1)
        success = run_specific_test(args.target)

    if success:
        print(f"\n🎉 Test run completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Test run failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()