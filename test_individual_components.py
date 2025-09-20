#!/usr/bin/env python3
"""
Dynamic Taxonomy RAG System v1.8.1
Individual Component Testing Script

이 스크립트는 13개 주요 컴포넌트를 개별적으로 테스트합니다.
"""

import asyncio
import sys
import os
import traceback
from pathlib import Path

# Add API directory to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "api"))

class ComponentTester:
    """Individual component testing class"""

    def __init__(self):
        self.test_results = {}
        self.failed_imports = []

    async def test_import(self, module_name, description):
        """Test if a module can be imported successfully"""
        try:
            if module_name.startswith('routers.'):
                # For router modules
                __import__(module_name)
                self.test_results[module_name] = {
                    'status': 'PASS',
                    'description': description,
                    'error': None
                }
                print(f"[PASS] {module_name}: {description}")
                return True
            else:
                # For regular modules
                __import__(module_name)
                self.test_results[module_name] = {
                    'status': 'PASS',
                    'description': description,
                    'error': None
                }
                print(f"[PASS] {module_name}: {description}")
                return True

        except Exception as e:
            self.test_results[module_name] = {
                'status': 'FAIL',
                'description': description,
                'error': str(e)
            }
            self.failed_imports.append(module_name)
            print(f"[FAIL] {module_name}: {description} - ERROR: {str(e)}")
            return False

    async def test_basic_functionality(self, module_name, test_func):
        """Test basic functionality of a module"""
        try:
            result = await test_func()
            print(f"[PASS] {module_name} functionality test passed")
            return True
        except Exception as e:
            print(f"[FAIL] {module_name} functionality test failed: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all component tests"""
        print("=" * 60)
        print("Dynamic Taxonomy RAG v1.8.1 - Component Testing")
        print("=" * 60)

        # Test 1: Health Router
        await self.test_import('routers.health', 'Health Check Router')

        # Test 2: Database Module
        await self.test_import('database', 'Database Connections & Models')

        # Test 3: Search Router
        await self.test_import('routers.search', 'Hybrid Search Engine Router')

        # Test 4: Classification Router
        await self.test_import('routers.classify', 'Document Classification Router')

        # Test 5: Taxonomy Router
        await self.test_import('routers.taxonomy', 'Taxonomy DAG Management Router')

        # Test 6: Ingestion Router
        await self.test_import('routers.ingestion', 'Document Ingestion Router')

        # Test 7: API Dependencies
        await self.test_import('deps', 'API Security & Dependencies')

        # Test 8: Monitoring Router
        await self.test_import('routers.monitoring', 'System Monitoring Router')

        # Test 9: Batch Search Router
        await self.test_import('routers.batch_search', 'Batch Search Processing Router')

        # Test 10: Evaluation Router
        await self.test_import('routers.evaluation', 'RAG Evaluation Router')

        # Test 11: Agent Factory Router
        await self.test_import('routers.agent_factory_router', 'Agent Factory Router')

        # Test 12: Orchestration Router
        await self.test_import('routers.orchestration_router', 'System Orchestration Router')

        # Test 13: Admin API Keys Router
        await self.test_import('routers.admin.api_keys', 'Admin API Keys Management Router')

        # Print summary
        print("\n" + "=" * 60)
        print("COMPONENT TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed_tests = total_tests - passed_tests

        print(f"Total Components Tested: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if self.failed_imports:
            print("\nFAILED COMPONENTS:")
            for module in self.failed_imports:
                result = self.test_results[module]
                print(f"  - {module}: {result['error']}")

        print("\nDETAILED RESULTS:")
        for module, result in self.test_results.items():
            status_icon = "[PASS]" if result['status'] == 'PASS' else "[FAIL]"
            print(f"  {status_icon} {module}: {result['description']}")

        return passed_tests == total_tests

async def main():
    """Main test function"""
    tester = ComponentTester()
    success = await tester.run_all_tests()

    if success:
        print("\n[SUCCESS] All components imported successfully!")
        print("System ready for integration testing.")
    else:
        print("\n[WARNING] Some components failed to import.")
        print("Fix the failed components before proceeding to integration tests.")

    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)