"""
Dynamic Taxonomy RAG API Client SDK Examples

This module provides comprehensive examples for interacting with the
Dynamic Taxonomy RAG API v1.8.1 using various programming languages
and frameworks.

Features:
- Python async/sync clients
- JavaScript/TypeScript examples
- Authentication handling
- Error handling and retry logic
- Rate limiting considerations
- Response streaming for large datasets
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import aiohttp
import requests
from pydantic import BaseModel


# Configuration and Models

class APIEnvironment(Enum):
    """API environment configurations"""
    DEVELOPMENT = "http://localhost:8000"
    STAGING = "https://staging-api.dt-rag.com"
    PRODUCTION = "https://api.dt-rag.com"


@dataclass
class APIConfig:
    """API client configuration"""
    base_url: str
    api_key: Optional[str] = None
    jwt_token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_requests: int = 100
    rate_limit_window: int = 60


class SearchRequest(BaseModel):
    """Search request model"""
    q: str
    max_results: int = 10
    search_type: str = "hybrid"
    taxonomy_filters: Optional[List[str]] = None


class ClassifyRequest(BaseModel):
    """Classification request model"""
    text: str
    taxonomy_version: Optional[str] = None


# Python Async Client

class DTRAGAsyncClient:
    """Asynchronous client for Dynamic Taxonomy RAG API"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._window_start = time.time()

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=self._get_headers()
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "dt-rag-python-client/1.8.1"
        }

        if self.config.jwt_token:
            headers["Authorization"] = f"Bearer {self.config.jwt_token}"
        elif self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        return headers

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        current_time = time.time()

        # Reset window if needed
        if current_time - self._window_start >= self.config.rate_limit_window:
            self._request_count = 0
            self._window_start = current_time

        # Check rate limit
        if self._request_count >= self.config.rate_limit_requests:
            sleep_time = self.config.rate_limit_window - (current_time - self._window_start)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._window_start = time.time()

        self._request_count += 1

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        await self._check_rate_limit()

        url = f"{self.config.base_url}{endpoint}"
        retries = 0

        while retries <= self.config.max_retries:
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get("Retry-After", 60))
                        await asyncio.sleep(retry_after)
                        retries += 1
                        continue

                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                if retries >= self.config.max_retries:
                    raise
                retries += 1
                await asyncio.sleep(2 ** retries)  # Exponential backoff

    # API Methods

    async def search(self, request: SearchRequest) -> Dict[str, Any]:
        """Perform hybrid search"""
        return await self._make_request(
            "POST",
            "/api/v1/search",
            json=request.dict()
        )

    async def classify(self, request: ClassifyRequest) -> Dict[str, Any]:
        """Classify document chunk"""
        return await self._make_request(
            "POST",
            "/api/v1/classify",
            json=request.dict()
        )

    async def get_taxonomy_tree(self, version: str) -> List[Dict[str, Any]]:
        """Get taxonomy tree for version"""
        return await self._make_request(
            "GET",
            f"/api/v1/taxonomy/{version}/tree"
        )

    async def execute_pipeline(self, query: str, **kwargs) -> Dict[str, Any]:
        """Execute RAG pipeline"""
        payload = {"query": query, **kwargs}
        return await self._make_request(
            "POST",
            "/api/v1/pipeline/execute",
            json=payload
        )

    async def create_agent(self, categories: List[List[str]], **kwargs) -> Dict[str, Any]:
        """Create agent from taxonomy categories"""
        payload = {"node_paths": categories, **kwargs}
        return await self._make_request(
            "POST",
            "/api/v1/agents/from-category",
            json=payload
        )

    async def get_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return await self._make_request("GET", "/health")

    async def get_monitoring_health(self) -> Dict[str, Any]:
        """Get detailed monitoring health"""
        return await self._make_request("GET", "/api/v1/monitoring/health")


# Python Sync Client

class DTRAGSyncClient:
    """Synchronous client for Dynamic Taxonomy RAG API"""

    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(self._get_headers())

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "dt-rag-python-client/1.8.1"
        }

        if self.config.jwt_token:
            headers["Authorization"] = f"Bearer {self.config.jwt_token}"
        elif self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        return headers

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.config.base_url}{endpoint}"
        retries = 0

        while retries <= self.config.max_retries:
            try:
                response = self.session.request(
                    method, url, timeout=self.config.timeout, **kwargs
                )

                if response.status_code == 429:  # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    time.sleep(retry_after)
                    retries += 1
                    continue

                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                if retries >= self.config.max_retries:
                    raise
                retries += 1
                time.sleep(2 ** retries)  # Exponential backoff

    def search(self, request: SearchRequest) -> Dict[str, Any]:
        """Perform hybrid search"""
        return self._make_request("POST", "/api/v1/search", json=request.dict())

    def classify(self, request: ClassifyRequest) -> Dict[str, Any]:
        """Classify document chunk"""
        return self._make_request("POST", "/api/v1/classify", json=request.dict())


# Usage Examples

async def async_client_example():
    """Example usage of async client"""
    config = APIConfig(
        base_url=APIEnvironment.DEVELOPMENT.value,
        api_key="your-api-key-here",
        timeout=30
    )

    async with DTRAGAsyncClient(config) as client:
        # Health check
        health = await client.get_health()
        print(f"API Health: {health['status']}")

        # Search example
        search_request = SearchRequest(
            q="machine learning algorithms",
            max_results=5,
            search_type="hybrid"
        )
        search_results = await client.search(search_request)
        print(f"Found {len(search_results.get('hits', []))} search results")

        # Classification example
        classify_request = ClassifyRequest(
            text="This document discusses neural networks and deep learning."
        )
        classification = await client.classify(classify_request)
        print(f"Classification: {classification.get('canonical', [])}")

        # Get taxonomy tree
        taxonomy = await client.get_taxonomy_tree("1.8.1")
        print(f"Taxonomy has {len(taxonomy)} nodes")

        # Execute RAG pipeline
        pipeline_result = await client.execute_pipeline(
            "What are the latest trends in AI?"
        )
        print(f"Pipeline response: {pipeline_result.get('answer', '')[:100]}...")


def sync_client_example():
    """Example usage of sync client"""
    config = APIConfig(
        base_url=APIEnvironment.DEVELOPMENT.value,
        jwt_token="your-jwt-token-here"
    )

    client = DTRAGSyncClient(config)

    # Search example
    search_request = SearchRequest(q="quantum computing", max_results=3)
    results = client.search(search_request)
    print(f"Search returned {len(results.get('hits', []))} results")


# JavaScript/TypeScript Example (as string template)

JAVASCRIPT_EXAMPLE = '''
// JavaScript/TypeScript Client Example
// Dynamic Taxonomy RAG API v1.8.1

class DTRAGClient {
    constructor(config) {
        this.baseUrl = config.baseUrl;
        this.apiKey = config.apiKey;
        this.jwtToken = config.jwtToken;
        this.timeout = config.timeout || 30000;
    }

    _getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'dt-rag-js-client/1.8.1'
        };

        if (this.jwtToken) {
            headers['Authorization'] = `Bearer ${this.jwtToken}`;
        } else if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }

        return headers;
    }

    async _makeRequest(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: this._getHeaders(),
            timeout: this.timeout
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // API Methods
    async search(query, options = {}) {
        const payload = {
            q: query,
            max_results: options.maxResults || 10,
            search_type: options.searchType || 'hybrid',
            taxonomy_filters: options.taxonomyFilters
        };

        return await this._makeRequest('POST', '/api/v1/search', payload);
    }

    async classify(text, taxonomyVersion = null) {
        const payload = { text, taxonomy_version: taxonomyVersion };
        return await this._makeRequest('POST', '/api/v1/classify', payload);
    }

    async getTaxonomyTree(version) {
        return await this._makeRequest('GET', `/api/v1/taxonomy/${version}/tree`);
    }

    async executePipeline(query, options = {}) {
        const payload = { query, ...options };
        return await this._makeRequest('POST', '/api/v1/pipeline/execute', payload);
    }

    async getHealth() {
        return await this._makeRequest('GET', '/health');
    }
}

// Usage Example
async function example() {
    const client = new DTRAGClient({
        baseUrl: 'http://localhost:8000',
        apiKey: 'your-api-key-here'
    });

    try {
        // Health check
        const health = await client.getHealth();
        console.log('API Status:', health.status);

        // Search
        const searchResults = await client.search('artificial intelligence', {
            maxResults: 5,
            searchType: 'hybrid'
        });
        console.log(`Found ${searchResults.hits.length} results`);

        // Classification
        const classification = await client.classify(
            'This paper presents a novel approach to natural language processing.'
        );
        console.log('Category:', classification.canonical);

    } catch (error) {
        console.error('Error:', error.message);
    }
}
'''

# cURL Examples

CURL_EXAMPLES = '''
# cURL Examples for Dynamic Taxonomy RAG API v1.8.1

# Health Check
curl -X GET http://localhost:8000/health

# Search with API key
curl -X POST http://localhost:8000/api/v1/search \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your-api-key" \\
  -d '{
    "q": "machine learning",
    "max_results": 5,
    "search_type": "hybrid"
  }'

# Classification with JWT token
curl -X POST http://localhost:8000/api/v1/classify \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-jwt-token" \\
  -d '{
    "text": "This document discusses neural networks."
  }'

# Get taxonomy tree
curl -X GET http://localhost:8000/api/v1/taxonomy/1.8.1/tree

# Execute RAG pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/execute \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-jwt-token" \\
  -d '{
    "query": "What are the latest AI trends?",
    "taxonomy_version": "1.8.1"
  }'

# Create agent from categories
curl -X POST http://localhost:8000/api/v1/agents/from-category \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-jwt-token" \\
  -d '{
    "node_paths": [["Technology", "AI", "Machine Learning"]],
    "name": "ML Expert Agent"
  }'

# Get monitoring health
curl -X GET http://localhost:8000/api/v1/monitoring/health
'''


if __name__ == "__main__":
    # Run async example
    print("🚀 Running Dynamic Taxonomy RAG API client examples")
    print("=" * 60)

    print("\n📝 JavaScript Example:")
    print(JAVASCRIPT_EXAMPLE)

    print("\n🌐 cURL Examples:")
    print(CURL_EXAMPLES)

    print("\n🐍 Running Python async example:")
    try:
        asyncio.run(async_client_example())
    except Exception as e:
        print(f"Note: {e} (API server may not be running)")

    print("\n✅ Examples completed!")
    print("\n💡 To use these examples:")
    print("1. Start the API server: python main.py")
    print("2. Replace 'your-api-key-here' with your actual API key")
    print("3. Replace 'your-jwt-token-here' with your actual JWT token")
    print("4. Modify endpoints and parameters as needed")