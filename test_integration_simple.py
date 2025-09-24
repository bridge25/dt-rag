"""
Simple integration test to verify test environment
"""

import pytest
import sys
from pathlib import Path

def test_basic_functionality():
    """Test that basic Python functionality works"""
    assert 1 + 1 == 2

def test_python_path():
    """Test that Python path includes current directory"""
    current_dir = str(Path.cwd())
    assert any(current_dir in path for path in sys.path), f"Current dir {current_dir} not in sys.path"

def test_pytest_working():
    """Test that pytest is working correctly"""
    assert True

def test_imports_available():
    """Test that basic imports work"""
    import json
    import os
    import sys
    assert json.dumps({"test": True}) == '{"test": true}'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])