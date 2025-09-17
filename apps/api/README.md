# Dynamic Taxonomy RAG API v1.8.1

A comprehensive RESTful API for the Dynamic Taxonomy RAG system, providing scalable and secure endpoints for taxonomy management, hybrid search, document classification, orchestration, agent factory, and real-time monitoring.

## 🌟 Features

### Core Capabilities
- **🔍 Hybrid Search**: BM25 + vector search with semantic reranking
- **📚 Taxonomy Management**: Hierarchical taxonomy operations with versioning
- **🤖 Classification Pipeline**: ML-based document classification with HITL support
- **🔄 RAG Orchestration**: LangGraph-based 7-step RAG pipeline
- **🏭 Agent Factory**: Dynamic agent creation and management
- **📊 Monitoring & Observability**: Real-time system monitoring and analytics

### Technical Features
- **🔐 Authentication**: JWT Bearer tokens, API keys, OAuth 2.0
- **⚡ Performance**: Redis caching, rate limiting, async processing
- **🛡️ Security**: GDPR/CCPA compliance, PII detection, audit logging
- **📖 Documentation**: OpenAPI 3.0.3 with interactive Swagger UI
- **🧪 Testing**: Comprehensive test suite with performance benchmarks

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL with pgvector extension
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd dt-rag/apps/api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the API server**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Accessing Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Spec**: http://localhost:8000/api/v1/openapi.json

## 📋 API Endpoints

### Bridge Pack Compatibility
The API maintains full compatibility with the Bridge Pack specification:

```
GET  /healthz                           # Health check
POST /classify                          # Document classification
POST /search                            # Document search
GET  /taxonomy/{version}/tree           # Taxonomy tree
POST /ingestion/upload                  # Document upload
POST /ingestion/urls                    # URL ingestion
GET  /ingestion/status/{job_id}         # Ingestion status
```

### Comprehensive API v1
New comprehensive endpoints with enhanced functionality:

#### Taxonomy Management
```
GET  /api/v1/taxonomy/versions          # List taxonomy versions
GET  /api/v1/taxonomy/{version}/tree    # Get taxonomy tree
GET  /api/v1/taxonomy/{version}/statistics  # Taxonomy statistics
GET  /api/v1/taxonomy/{version}/validate    # Validate taxonomy
GET  /api/v1/taxonomy/{base_version}/compare/{target_version}  # Compare versions
GET  /api/v1/taxonomy/{version}/search  # Search taxonomy nodes
```

#### Search
```
POST /api/v1/search                     # Hybrid search
GET  /api/v1/search/analytics           # Search analytics
GET  /api/v1/search/config              # Search configuration
PUT  /api/v1/search/config              # Update search config
POST /api/v1/search/reindex             # Trigger reindexing
POST /api/v1/search/suggest             # Search suggestions
GET  /api/v1/search/status              # Search system status
```

#### Classification
```
POST /api/v1/classify                   # Classify document chunk
POST /api/v1/classify/batch             # Batch classification
GET  /api/v1/classify/hitl/tasks        # Get HITL tasks
POST /api/v1/classify/hitl/review       # Submit HITL review
GET  /api/v1/classify/analytics         # Classification analytics
GET  /api/v1/classify/confidence/{chunk_id}  # Confidence analysis
GET  /api/v1/classify/status            # Classification system status
```

#### Orchestration
```
POST /api/v1/pipeline/execute           # Execute RAG pipeline
POST /api/v1/pipeline/execute/async     # Async pipeline execution
GET  /api/v1/pipeline/jobs/{job_id}     # Get pipeline job status
GET  /api/v1/pipeline/config            # Get pipeline configuration
PUT  /api/v1/pipeline/config            # Update pipeline configuration
GET  /api/v1/pipeline/analytics         # Pipeline analytics
GET  /api/v1/pipeline/status            # Pipeline system status
```

#### Agent Factory
```
POST /api/v1/agents/from-category       # Create agent from categories
GET  /api/v1/agents                     # List agents
GET  /api/v1/agents/{agent_id}          # Get agent details
PUT  /api/v1/agents/{agent_id}          # Update agent
DELETE /api/v1/agents/{agent_id}        # Delete agent
GET  /api/v1/agents/{agent_id}/metrics  # Agent performance metrics
POST /api/v1/agents/{agent_id}/activate    # Activate agent
POST /api/v1/agents/{agent_id}/deactivate  # Deactivate agent
GET  /api/v1/agents/factory/status      # Factory system status
```

#### Monitoring
```
GET  /api/v1/monitoring/health          # System health status
GET  /api/v1/monitoring/metrics/system  # System performance metrics
GET  /api/v1/monitoring/metrics/api     # API performance metrics
GET  /api/v1/monitoring/metrics/endpoints  # Endpoint statistics
GET  /api/v1/monitoring/alerts          # System alerts
POST /api/v1/monitoring/alerts/{alert_id}/acknowledge  # Acknowledge alert
GET  /api/v1/monitoring/trends          # Performance trends
GET  /api/v1/monitoring/status          # Monitoring system status
```

#### Utility
```
GET  /health                            # Basic health check
GET  /                                  # API root with system info
GET  /api/versions                      # List API versions
GET  /api/v1/rate-limits                # Rate limiting information
```

## 🔐 Authentication

### API Key Authentication
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/search
```

### JWT Bearer Token
```bash
curl -H "Authorization: Bearer your-jwt-token" http://localhost:8000/api/v1/agents/from-category
```

### OAuth 2.0
See the OAuth 2.0 section in the API documentation for detailed flow information.

## 📊 Usage Examples

### Python Client
```python
import asyncio
from sdk_examples import DTRAGAsyncClient, APIConfig, SearchRequest

async def main():
    config = APIConfig(
        base_url="http://localhost:8000",
        api_key="your-api-key"
    )

    async with DTRAGAsyncClient(config) as client:
        # Health check
        health = await client.get_health()
        print(f"API Status: {health['status']}")

        # Search
        search_request = SearchRequest(
            q="machine learning algorithms",
            max_results=5,
            search_type="hybrid"
        )
        results = await client.search(search_request)
        print(f"Found {len(results['hits'])} results")

asyncio.run(main())
```

### JavaScript/Node.js
```javascript
const client = new DTRAGClient({
    baseUrl: 'http://localhost:8000',
    apiKey: 'your-api-key'
});

// Search example
const results = await client.search('artificial intelligence', {
    maxResults: 5,
    searchType: 'hybrid'
});
console.log(`Found ${results.hits.length} results`);
```

### cURL Examples
```bash
# Search with hybrid search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "q": "machine learning",
    "max_results": 5,
    "search_type": "hybrid"
  }'

# Execute RAG pipeline
curl -X POST http://localhost:8000/api/v1/pipeline/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "query": "What are the latest AI trends?",
    "taxonomy_version": "1.8.1"
  }'
```

## 🧪 Testing

### Run Test Suite
```bash
# Install testing dependencies
pip install pytest pytest-asyncio aiohttp

# Run all tests
python testing_guide.py

# Run specific tests with pytest
pytest testing_guide.py::TestDTRAGAPI::test_search_endpoint

# Run performance tests
python testing_guide.py --performance
```

### Generate OpenAPI Specification
```bash
# Generate JSON and YAML specs
python generate_openapi.py --format both --output-dir ./docs

# Validate specification
python generate_openapi.py --validate
```

## 📖 Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Specification
- **JSON**: http://localhost:8000/api/v1/openapi.json
- **YAML**: Generated via `generate_openapi.py`

### Client SDKs
- **Python**: See `sdk_examples.py` for async/sync clients
- **JavaScript**: Example client implementation included
- **cURL**: Complete command-line examples

## ⚡ Performance

### Rate Limits
- **Standard Tier**: 100 requests/minute, 5,000 requests/hour
- **Premium Tier**: 1,000 requests/minute, 50,000 requests/hour
- **Enterprise**: Custom limits available

### Response Time Targets
- **Search**: < 100ms p95
- **Classification**: < 200ms p95
- **Pipeline Execution**: < 4s p95
- **Taxonomy Operations**: < 50ms p95

### Caching
- Redis-based response caching
- Configurable TTL per endpoint
- Cache invalidation on data updates

## 🛡️ Security

### Data Protection
- **Encryption**: TLS 1.3 for data in transit
- **PII Detection**: Automatic sensitive data identification
- **Audit Logging**: Comprehensive request logging

### Compliance
- **GDPR**: Data privacy controls and right to deletion
- **CCPA**: California privacy compliance
- **SOC 2**: Security controls and monitoring

### Input Validation
- **Request Validation**: Pydantic schema validation
- **Rate Limiting**: Per-user and global limits
- **CORS**: Configurable cross-origin policies

## 🔧 Configuration

### Environment Variables
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dtrag
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET_KEY=your-secret-key
API_KEY_SALT=your-salt

# Performance
RATE_LIMIT_REQUESTS_PER_MINUTE=100
CACHE_TTL_SECONDS=300

# Features
ENABLE_MONITORING=true
ENABLE_CACHING=true
DEBUG=false
```

### Configuration Files
- `config.py`: Main configuration management
- `.env`: Environment-specific settings
- `requirements.txt`: Python dependencies

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t dt-rag-api .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  dt-rag-api
```

### Production Considerations
- **Load Balancing**: Use nginx or cloud load balancers
- **Database**: PostgreSQL with pgvector extension
- **Caching**: Redis cluster for high availability
- **Monitoring**: Prometheus/Grafana for metrics
- **Logging**: Structured logging with log aggregation

## 📊 Monitoring

### Health Checks
- **Basic**: `GET /health`
- **Detailed**: `GET /api/v1/monitoring/health`
- **Components**: Database, Redis, search index, models

### Metrics
- **System**: CPU, memory, disk usage
- **API**: Request rate, response times, error rates
- **Business**: Search queries, classifications, pipeline executions

### Alerts
- **Performance**: Response time degradation
- **Errors**: High error rates
- **Resources**: Resource utilization thresholds

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a virtual environment
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `python testing_guide.py`
5. Submit pull request

### Code Standards
- **Style**: PEP 8 compliance
- **Type Hints**: Full type annotation
- **Documentation**: Comprehensive docstrings
- **Testing**: 90%+ test coverage

## 📝 Changelog

### v1.8.1 (Current)
- ✅ Complete OpenAPI 3.0.3 specification
- ✅ Comprehensive API documentation
- ✅ Bridge Pack compatibility maintained
- ✅ Enhanced authentication and authorization
- ✅ Real-time monitoring and observability
- ✅ Performance optimization and caching
- ✅ Client SDKs and testing utilities

### Upcoming Features
- GraphQL API support
- WebSocket real-time updates
- Advanced analytics dashboard
- Multi-language client SDKs

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
- **Documentation**: http://localhost:8000/docs
- **Issues**: Create GitHub issue
- **API Status**: http://localhost:8000/api/v1/monitoring/health

### Contact
- **Team**: A Team
- **Email**: api-support@dt-rag.com
- **Discord**: [Community Server]

---

**Dynamic Taxonomy RAG API v1.8.1** - Built for scale, designed for developers, optimized for performance.