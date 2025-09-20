#!/usr/bin/env python3
"""
CI/CD Migration Helper Script
Provides enhanced migration testing and validation for GitHub Actions
"""

import os
import sys
import time
import subprocess
import argparse
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationHelper:
    """Helper class for managing database migrations in CI/CD environments."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        self.is_ci = os.getenv('CI', '').lower() == 'true'
        self.is_github_actions = os.getenv('GITHUB_ACTIONS', '').lower() == 'true'
        
    def log_info(self, message: str) -> None:
        """Log info message with CI-friendly formatting."""
        if self.is_github_actions:
            print(f"::info::{message}")
        logger.info(message)
        
    def log_error(self, message: str) -> None:
        """Log error message with CI-friendly formatting."""
        if self.is_github_actions:
            print(f"::error::{message}")
        logger.error(message)
        
    def run_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Run command with proper error handling."""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def test_database_connection(self) -> bool:
        """Test database connection before running migrations."""
        if not self.database_url:
            self.log_error("No database URL provided")
            return False
            
        self.log_info("Testing database connection...")
        
        if 'postgresql' in self.database_url:
            try:
                import psycopg2
                conn = psycopg2.connect(self.database_url)
                conn.close()
                self.log_info("PostgreSQL connection test successful")
                return True
            except Exception as e:
                self.log_error(f"PostgreSQL connection test failed: {e}")
                return False
        
        return True
    
    def run_full_migration_test(self) -> bool:
        """Run complete migration test suite."""
        self.log_info("Starting migration test suite")
        
        if not self.test_database_connection():
            return False
            
        result = self.run_command("alembic upgrade head")
        if not result['success']:
            self.log_error(f"Migration failed: {result['stderr']}")
            return False
            
        self.log_info("Migration test completed successfully")
        return True

def main():
    """Main entry point."""
    helper = MigrationHelper()
    success = helper.run_full_migration_test()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
