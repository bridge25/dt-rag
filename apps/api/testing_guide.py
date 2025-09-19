"""
API Testing and Integration Guide for Dynamic Taxonomy RAG API v1.8.1

This module provides comprehensive testing utilities and integration guides
for the Dynamic Taxonomy RAG API including:

- Unit tests for individual endpoints
- Integration tests for complete workflows
- Performance testing and benchmarking
- Authentication testing
- Error handling validation
- Load testing scenarios
"""

import asyncio
import time
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import pytest
import aiohttp
import requests


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Performance testing metrics"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    requests_per_second: float


class APITester:
    """Comprehensive API testing utility"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.test_results: List[TestResult] = []

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def _async_request(self, session: aiohttp.ClientSession,
                           method: str, endpoint: str, **kwargs) -> TestResult:
        """Make async HTTP request and measure performance"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint}"
            async with session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                response_data = await response.json()

                return TestResult(
                    test_name=f"{method} {endpoint}",
                    success=response.status < 400,
                    response_time=response_time,
                    status_code=response.status,
                    response_data=response_data
                )

        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                test_name=f"{method} {endpoint}",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )

    def _sync_request(self, method: str, endpoint: str, **kwargs) -> TestResult:
        """Make sync HTTP request and measure performance"""
        start_time = time.time()

        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(
                method, url,
                headers=self._get_headers(),
                timeout=30,
                **kwargs
            )
            response_time = time.time() - start_time

            return TestResult(
                test_name=f"{method} {endpoint}",
                success=response.status_code < 400,
                response_time=response_time,
                status_code=response.status_code,
                response_data=response.json() if response.content else None
            )

        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                test_name=f"{method} {endpoint}",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )

    # Basic Endpoint Tests

    def test_health_check(self) -> TestResult:
        """Test health check endpoint"""
        result = self._sync_request("GET", "/health")
        self.test_results.append(result)
        return result

    def test_api_root(self) -> TestResult:
        """Test API root endpoint"""
        result = self._sync_request("GET", "/")
        self.test_results.append(result)
        return result

    def test_api_versions(self) -> TestResult:
        """Test API versions endpoint"""
        result = self._sync_request("GET", "/api/versions")
        self.test_results.append(result)
        return result

    def test_openapi_spec(self) -> TestResult:
        """Test OpenAPI specification endpoint"""
        result = self._sync_request("GET", "/api/v1/openapi.json")
        self.test_results.append(result)
        return result

    # Functional Tests

    def test_search_functionality(self) -> TestResult:
        """Test search endpoint functionality"""
        payload = {
            "q": "artificial intelligence",
            "max_results": 5,
            "search_type": "hybrid"
        }
        result = self._sync_request("POST", "/api/v1/search", json=payload)
        self.test_results.append(result)
        return result

    def test_classification_functionality(self) -> TestResult:
        """Test classification endpoint functionality"""
        payload = {
            "text": "This document discusses machine learning algorithms and neural networks."
        }
        result = self._sync_request("POST", "/api/v1/classify", json=payload)
        self.test_results.append(result)
        return result

    def test_taxonomy_tree(self) -> TestResult:
        """Test taxonomy tree endpoint"""
        result = self._sync_request("GET", "/api/v1/taxonomy/1.8.1/tree")
        self.test_results.append(result)
        return result

    def test_pipeline_execution(self) -> TestResult:
        """Test RAG pipeline execution"""
        payload = {
            "query": "What are the benefits of machine learning?",
            "taxonomy_version": "1.8.1"
        }
        result = self._sync_request("POST", "/api/v1/pipeline/execute", json=payload)
        self.test_results.append(result)
        return result

    # Error Handling Tests

    def test_invalid_endpoint(self) -> TestResult:
        """Test 404 error handling"""
        result = self._sync_request("GET", "/api/v1/nonexistent")
        self.test_results.append(result)
        return result

    def test_invalid_method(self) -> TestResult:
        """Test 405 error handling"""
        result = self._sync_request("DELETE", "/api/v1/search")
        self.test_results.append(result)
        return result

    def test_invalid_payload(self) -> TestResult:
        """Test 422 error handling with invalid data"""
        payload = {"invalid": "data"}
        result = self._sync_request("POST", "/api/v1/search", json=payload)
        self.test_results.append(result)
        return result

    def test_empty_search_query(self) -> TestResult:
        """Test validation error with empty search query"""
        payload = {"q": "", "max_results": 5}
        result = self._sync_request("POST", "/api/v1/search", json=payload)
        self.test_results.append(result)
        return result

    # Authentication Tests

    def test_unauthorized_access(self) -> TestResult:
        """Test unauthorized access to protected endpoints"""
        # Remove API key for this test
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/agents/from-category",
                headers=headers,
                json={"node_paths": [["Technology", "AI"]]},
                timeout=30
            )

            result = TestResult(
                test_name="Unauthorized Access Test",
                success=response.status_code in [401, 403],  # Expect auth error
                response_time=0.0,
                status_code=response.status_code,
                response_data=response.json() if response.content else None
            )

        except Exception as e:
            result = TestResult(
                test_name="Unauthorized Access Test",
                success=False,
                response_time=0.0,
                error_message=str(e)
            )

        self.test_results.append(result)
        return result

    # Performance Tests

    async def performance_test_concurrent_requests(self,
                                                 concurrent_requests: int = 10,
                                                 total_requests: int = 100) -> PerformanceMetrics:
        """Test concurrent request performance"""
        print(f"🚀 Running performance test: {concurrent_requests} concurrent, {total_requests} total")

        async def make_request(session):
            return await self._async_request(
                session, "GET", "/health",
                headers=self._get_headers()
            )

        # Execute concurrent requests
        start_time = time.time()
        results = []

        async with aiohttp.ClientSession() as session:
            for batch_start in range(0, total_requests, concurrent_requests):
                batch_size = min(concurrent_requests, total_requests - batch_start)
                batch_tasks = [make_request(session) for _ in range(batch_size)]
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend(batch_results)

        total_time = time.time() - start_time

        # Calculate metrics
        successful_results = [r for r in results if r.success]
        response_times = [r.response_time for r in successful_results]

        if response_times:
            return PerformanceMetrics(
                total_requests=len(results),
                successful_requests=len(successful_results),
                failed_requests=len(results) - len(successful_results),
                avg_response_time=statistics.mean(response_times),
                min_response_time=min(response_times),
                max_response_time=max(response_times),
                p95_response_time=statistics.quantiles(response_times, n=20)[18],
                requests_per_second=len(successful_results) / total_time
            )
        else:
            return PerformanceMetrics(
                total_requests=len(results),
                successful_requests=0,
                failed_requests=len(results),
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p95_response_time=0.0,
                requests_per_second=0.0
            )

    def load_test_search_endpoint(self, duration_seconds: int = 60) -> List[TestResult]:
        """Load test the search endpoint for specified duration"""
        print(f"🔥 Running load test for {duration_seconds} seconds")

        results = []
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration_seconds:
            payload = {
                "q": f"test query {request_count}",
                "max_results": 3,
                "search_type": "hybrid"
            }

            result = self._sync_request("POST", "/api/v1/search", json=payload)
            results.append(result)
            request_count += 1

            # Small delay to avoid overwhelming the server
            time.sleep(0.1)

        return results

    # Integration Tests

    def integration_test_complete_workflow(self) -> List[TestResult]:
        """Test complete API workflow"""
        print("🔄 Running complete workflow integration test")

        workflow_results = []

        # Step 1: Health check
        health_result = self.test_health_check()
        workflow_results.append(health_result)

        if not health_result.success:
            print("❌ Health check failed, stopping workflow test")
            return workflow_results

        # Step 2: Get taxonomy tree
        taxonomy_result = self.test_taxonomy_tree()
        workflow_results.append(taxonomy_result)

        # Step 3: Perform search
        search_result = self.test_search_functionality()
        workflow_results.append(search_result)

        # Step 4: Classify text
        classify_result = self.test_classification_functionality()
        workflow_results.append(classify_result)

        # Step 5: Execute pipeline
        pipeline_result = self.test_pipeline_execution()
        workflow_results.append(pipeline_result)

        return workflow_results

    # Test Reporting

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        if not self.test_results:
            return {"error": "No test results available"}

        successful_tests = [r for r in self.test_results if r.success]
        failed_tests = [r for r in self.test_results if not r.success]
        response_times = [r.response_time for r in successful_tests]

        report = {
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.test_results) * 100
            },
            "performance": {
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0
            },
            "failed_tests": [
                {
                    "test_name": r.test_name,
                    "error_message": r.error_message,
                    "status_code": r.status_code
                }
                for r in failed_tests
            ],
            "test_details": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "response_time": r.response_time,
                    "status_code": r.status_code
                }
                for r in self.test_results
            ]
        }

        return report

    def print_test_report(self):
        """Print formatted test report"""
        report = self.generate_test_report()

        print("\n" + "="*60)
        print("📊 API TEST REPORT")
        print("="*60)

        print(f"\n📈 Summary:")
        print(f"  Total Tests: {report['summary']['total_tests']}")
        print(f"  Successful: {report['summary']['successful_tests']}")
        print(f"  Failed: {report['summary']['failed_tests']}")
        print(f"  Success Rate: {report['summary']['success_rate']:.1f}%")

        print(f"\n⚡ Performance:")
        print(f"  Avg Response Time: {report['performance']['avg_response_time']:.3f}s")
        print(f"  Min Response Time: {report['performance']['min_response_time']:.3f}s")
        print(f"  Max Response Time: {report['performance']['max_response_time']:.3f}s")
        print(f"  P95 Response Time: {report['performance']['p95_response_time']:.3f}s")

        if report['failed_tests']:
            print(f"\n❌ Failed Tests:")
            for test in report['failed_tests']:
                print(f"  - {test['test_name']}: {test['error_message']}")


# Pytest Integration

class TestDTRAGAPI:
    """Pytest test class for automated testing"""

    @pytest.fixture
    def api_tester(self):
        """Pytest fixture for API tester"""
        return APITester("http://localhost:8000")

    def test_health_endpoint(self, api_tester):
        """Test health endpoint"""
        result = api_tester.test_health_check()
        assert result.success
        assert result.status_code == 200

    def test_search_endpoint(self, api_tester):
        """Test search endpoint"""
        result = api_tester.test_search_functionality()
        assert result.success
        assert result.status_code == 200

    def test_classification_endpoint(self, api_tester):
        """Test classification endpoint"""
        result = api_tester.test_classification_functionality()
        assert result.success
        assert result.status_code == 200

    def test_error_handling(self, api_tester):
        """Test error handling"""
        result = api_tester.test_invalid_endpoint()
        assert not result.success
        assert result.status_code == 404


# Main Testing Function

async def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive API Testing")
    print("="*60)

    tester = APITester("http://localhost:8000", api_key="test-api-key")

    # Basic functionality tests
    print("\n📋 Running Basic Functionality Tests...")
    tester.test_health_check()
    tester.test_api_root()
    tester.test_api_versions()
    tester.test_openapi_spec()

    # Endpoint functionality tests
    print("\n🔧 Running Endpoint Functionality Tests...")
    tester.test_search_functionality()
    tester.test_classification_functionality()
    tester.test_taxonomy_tree()
    tester.test_pipeline_execution()

    # Error handling tests
    print("\n⚠️ Running Error Handling Tests...")
    tester.test_invalid_endpoint()
    tester.test_invalid_method()
    tester.test_invalid_payload()
    tester.test_empty_search_query()

    # Authentication tests
    print("\n🔐 Running Authentication Tests...")
    tester.test_unauthorized_access()

    # Performance tests
    print("\n⚡ Running Performance Tests...")
    perf_metrics = await tester.performance_test_concurrent_requests(5, 25)
    print(f"Performance: {perf_metrics.requests_per_second:.2f} req/s, "
          f"avg: {perf_metrics.avg_response_time:.3f}s")

    # Integration test
    print("\n🔄 Running Integration Tests...")
    tester.integration_test_complete_workflow()

    # Generate and print report
    tester.print_test_report()

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    print("🧪 Dynamic Taxonomy RAG API Testing Guide")
    print("=" * 60)
    print()
    print("📚 Available testing options:")
    print("1. Run comprehensive tests: python testing_guide.py")
    print("2. Run pytest: pytest testing_guide.py")
    print("3. Import and use APITester class for custom tests")
    print()
    print("💡 Make sure the API server is running on localhost:8000")
    print()

    # Run comprehensive tests
    try:
        asyncio.run(run_comprehensive_tests())
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        print("💡 Make sure the API server is running: python main.py")