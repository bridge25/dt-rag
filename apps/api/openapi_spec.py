"""
OpenAPI 3.0.3 Specification Generator for Dynamic Taxonomy RAG v1.8.1

This module generates comprehensive OpenAPI specifications for all DT-RAG API endpoints
including authentication, versioning, examples, and complete schema definitions.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

def generate_openapi_spec() -> Dict[str, Any]:
    """
    Generate complete OpenAPI 3.0.3 specification for DT-RAG v1.8.1

    Returns:
        Complete OpenAPI specification dictionary
    """

    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Dynamic Taxonomy RAG API",
            "version": "1.8.1",
            "description": """
# Dynamic Taxonomy RAG API v1.8.1

A comprehensive RESTful API for the Dynamic Taxonomy RAG system providing:

- **Taxonomy Management**: Hierarchical taxonomy operations with DAG support
- **Document Ingestion**: Automated document processing and classification
- **Hybrid Search**: Combined BM25 and vector search with reranking
- **Classification Pipeline**: HITL-enabled document classification
- **LangGraph Orchestration**: 7-step RAG pipeline execution
- **Evaluation Framework**: RAGAS-based evaluation and A/B testing
- **Security & Compliance**: GDPR/CCPA compliant with comprehensive security
- **Monitoring & Observability**: Real-time metrics and performance tracking

## Key Features

- **High Performance**: p95 latency ≤ 100ms per endpoint
- **Scalable Architecture**: Microservices-based with async operations
- **Comprehensive Authentication**: JWT + OAuth 2.0 + API keys
- **Advanced Rate Limiting**: Tiered limits based on user type and endpoint complexity
- **Complete Validation**: Request/response schema validation with detailed error messages
- **Interactive Documentation**: Live API testing with realistic examples

## Authentication

All API endpoints (except public health checks) require authentication using one of:

1. **JWT Bearer Token**: For user-based authentication
2. **API Key**: For service-to-service communication
3. **OAuth 2.0**: For third-party integrations

## Rate Limiting

Default rate limits (can be customized per endpoint):
- **Authentication**: 5 requests/minute
- **Search Operations**: 100 requests/minute
- **Classification**: 50 requests/minute
- **Admin Operations**: 10 requests/minute

## Error Handling

All errors follow RFC 7807 Problem Details format with:
- Consistent error structure
- Meaningful error codes
- Actionable error messages
- Request correlation IDs
            """,
            "contact": {
                "name": "DT-RAG API Support",
                "email": "api-support@dt-rag.com",
                "url": "https://docs.dt-rag.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            },
            "termsOfService": "https://dt-rag.com/terms"
        },
        "servers": [
            {
                "url": "https://api.dt-rag.com/v1",
                "description": "Production server"
            },
            {
                "url": "https://staging-api.dt-rag.com/v1",
                "description": "Staging server"
            },
            {
                "url": "http://localhost:8000/api/v1",
                "description": "Development server"
            }
        ],
        "tags": [
            {
                "name": "Authentication",
                "description": "User authentication and session management"
            },
            {
                "name": "Taxonomy",
                "description": "Hierarchical taxonomy management and navigation"
            },
            {
                "name": "Search",
                "description": "Hybrid search operations with BM25 and vector search"
            },
            {
                "name": "Classification",
                "description": "Document classification with HITL support"
            },
            {
                "name": "Ingestion",
                "description": "Document ingestion and processing pipeline"
            },
            {
                "name": "Orchestration",
                "description": "LangGraph-based RAG pipeline execution"
            },
            {
                "name": "Evaluation",
                "description": "RAGAS evaluation and A/B testing framework"
            },
            {
                "name": "Monitoring",
                "description": "System metrics and observability"
            },
            {
                "name": "Security",
                "description": "Security management and compliance"
            },
            {
                "name": "Agent Factory",
                "description": "Dynamic agent creation and management"
            }
        ],
        "security": [
            {"BearerAuth": []},
            {"ApiKeyAuth": []},
            {"OAuth2": []}
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token authentication. Include in Authorization header: `Authorization: Bearer <token>`"
                },
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for service-to-service communication"
                },
                "OAuth2": {
                    "type": "oauth2",
                    "flows": {
                        "authorizationCode": {
                            "authorizationUrl": "https://auth.dt-rag.com/oauth/authorize",
                            "tokenUrl": "https://auth.dt-rag.com/oauth/token",
                            "scopes": {
                                "read": "Read access to API resources",
                                "write": "Write access to API resources",
                                "admin": "Administrative access to all resources"
                            }
                        }
                    }
                }
            },
            "schemas": generate_schemas(),
            "responses": generate_common_responses(),
            "parameters": generate_common_parameters(),
            "examples": generate_examples()
        },
        "paths": generate_api_paths()
    }

    return spec

def generate_schemas() -> Dict[str, Any]:
    """Generate all Pydantic-compatible schemas"""

    return {
        # Core Data Models
        "TaxonomyNode": {
            "type": "object",
            "required": ["node_id", "canonical_path", "name", "version", "created_at"],
            "properties": {
                "node_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Unique node identifier",
                    "example": "123e4567-e89b-12d3-a456-426614174000"
                },
                "canonical_path": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Full path from root to this node",
                    "example": ["Technology", "AI", "Machine Learning"]
                },
                "parent_id": {
                    "type": "string",
                    "format": "uuid",
                    "nullable": True,
                    "description": "Parent node identifier"
                },
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100,
                    "description": "Human-readable node name",
                    "example": "Machine Learning"
                },
                "version": {
                    "type": "string",
                    "pattern": "^\\d+\\.\\d+\\.\\d+$",
                    "description": "Semantic version",
                    "example": "1.8.1"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Classification confidence score",
                    "example": 0.85
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": True,
                    "description": "Additional node metadata",
                    "example": {
                        "description": "Machine learning algorithms and techniques",
                        "synonyms": ["ML", "Automated Learning"]
                    }
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Node creation timestamp"
                },
                "updated_at": {
                    "type": "string",
                    "format": "date-time",
                    "nullable": True,
                    "description": "Last update timestamp"
                }
            }
        },

        "SearchRequest": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 1000,
                    "description": "Search query text",
                    "example": "machine learning algorithms for classification"
                },
                "taxonomy_filters": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": "Taxonomy path filters to limit search scope",
                    "example": [["Technology", "AI"], ["Science", "Computer Science"]]
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                    "description": "Maximum number of results to return"
                },
                "search_type": {
                    "type": "string",
                    "enum": ["bm25", "vector", "hybrid"],
                    "default": "hybrid",
                    "description": "Type of search to perform"
                },
                "rerank_candidates": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 100,
                    "default": 50,
                    "description": "Number of candidates for reranking"
                }
            }
        },

        "SearchResponse": {
            "type": "object",
            "required": ["hits", "latency", "request_id"],
            "properties": {
                "hits": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/SearchHit"}
                },
                "latency": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Search latency in seconds",
                    "example": 0.045
                },
                "request_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Unique request identifier for tracking"
                },
                "total_candidates": {
                    "type": "integer",
                    "description": "Total number of candidates before reranking"
                },
                "sources_count": {
                    "type": "integer",
                    "description": "Number of unique sources"
                },
                "taxonomy_version": {
                    "type": "string",
                    "description": "Taxonomy version used for search"
                }
            }
        },

        "SearchHit": {
            "type": "object",
            "required": ["chunk_id", "score"],
            "properties": {
                "chunk_id": {
                    "type": "string",
                    "description": "Unique chunk identifier"
                },
                "score": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Relevance score"
                },
                "text": {
                    "type": "string",
                    "description": "Chunk text content"
                },
                "source": {"$ref": "#/components/schemas/SourceMeta"},
                "taxonomy_path": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Taxonomy classification path"
                }
            }
        },

        "SourceMeta": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"},
                "title": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "version": {"type": "string"},
                "span": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2,
                    "description": "Start and end positions in source document"
                }
            }
        },

        "ClassifyRequest": {
            "type": "object",
            "required": ["chunk_id", "text"],
            "properties": {
                "chunk_id": {
                    "type": "string",
                    "description": "Unique chunk identifier"
                },
                "text": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 10000,
                    "description": "Text content to classify"
                },
                "hint_paths": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": "Suggested taxonomy paths for classification hints"
                }
            }
        },

        "ClassifyResponse": {
            "type": "object",
            "required": ["canonical", "candidates", "confidence", "reasoning"],
            "properties": {
                "canonical": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Primary classification path"
                },
                "candidates": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/TaxonomyNode"},
                    "description": "Alternative classification candidates"
                },
                "hitl": {
                    "type": "boolean",
                    "default": False,
                    "description": "Requires human-in-the-loop review"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Classification confidence score"
                },
                "reasoning": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "description": "Classification reasoning steps"
                }
            }
        },

        "PipelineRequest": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 2000,
                    "description": "User query for RAG pipeline"
                },
                "taxonomy_version": {
                    "type": "string",
                    "description": "Specific taxonomy version to use",
                    "example": "1.8.1"
                },
                "agent_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Specific agent to use for pipeline execution"
                },
                "search_config": {
                    "type": "object",
                    "properties": {
                        "max_results": {"type": "integer", "default": 10},
                        "search_type": {"type": "string", "enum": ["hybrid", "bm25", "vector"], "default": "hybrid"}
                    }
                },
                "generation_config": {
                    "type": "object",
                    "properties": {
                        "temperature": {"type": "number", "minimum": 0.0, "maximum": 2.0, "default": 0.7},
                        "max_tokens": {"type": "integer", "minimum": 1, "maximum": 4000, "default": 1000}
                    }
                }
            }
        },

        "PipelineResponse": {
            "type": "object",
            "required": ["answer", "sources", "confidence", "cost", "latency"],
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Generated answer from RAG pipeline"
                },
                "sources": {
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/SearchHit"},
                    "description": "Source documents used for answer generation"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Answer confidence score"
                },
                "cost": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Processing cost in KRW"
                },
                "latency": {
                    "type": "number",
                    "minimum": 0.0,
                    "description": "Total processing latency in seconds"
                },
                "taxonomy_version": {
                    "type": "string",
                    "description": "Taxonomy version used"
                },
                "intent": {
                    "type": "string",
                    "description": "Detected user intent"
                },
                "pipeline_metadata": {
                    "type": "object",
                    "properties": {
                        "steps_executed": {"type": "array", "items": {"type": "string"}},
                        "step_latencies": {"type": "object"},
                        "retrieval_stats": {"type": "object"},
                        "generation_stats": {"type": "object"}
                    }
                }
            }
        },

        "AuthRequest": {
            "type": "object",
            "required": ["username", "password"],
            "properties": {
                "username": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 50,
                    "description": "Username or email address"
                },
                "password": {
                    "type": "string",
                    "minLength": 8,
                    "maxLength": 128,
                    "description": "User password"
                }
            }
        },

        "AuthResponse": {
            "type": "object",
            "required": ["access_token", "token_type", "expires_in"],
            "properties": {
                "access_token": {
                    "type": "string",
                    "description": "JWT access token"
                },
                "token_type": {
                    "type": "string",
                    "enum": ["bearer"],
                    "description": "Token type"
                },
                "expires_in": {
                    "type": "integer",
                    "description": "Token expiration time in seconds"
                },
                "refresh_token": {
                    "type": "string",
                    "description": "Refresh token for obtaining new access tokens"
                },
                "user_info": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "username": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "roles": {"type": "array", "items": {"type": "string"}},
                        "permissions": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        },

        "ErrorResponse": {
            "type": "object",
            "required": ["type", "title", "status"],
            "properties": {
                "type": {
                    "type": "string",
                    "format": "uri",
                    "description": "URI reference identifying the problem type",
                    "example": "https://dt-rag.com/problems/validation-error"
                },
                "title": {
                    "type": "string",
                    "description": "Short, human-readable summary of the problem",
                    "example": "Validation Error"
                },
                "status": {
                    "type": "integer",
                    "description": "HTTP status code",
                    "example": 400
                },
                "detail": {
                    "type": "string",
                    "description": "Human-readable explanation specific to this problem",
                    "example": "The 'query' field is required and cannot be empty"
                },
                "instance": {
                    "type": "string",
                    "format": "uri",
                    "description": "URI reference identifying the specific occurrence",
                    "example": "/api/v1/search"
                },
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "message": {"type": "string"},
                            "code": {"type": "string"}
                        }
                    },
                    "description": "Detailed validation errors"
                },
                "correlation_id": {
                    "type": "string",
                    "format": "uuid",
                    "description": "Request correlation ID for debugging"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Error occurrence timestamp"
                }
            }
        },

        "HealthResponse": {
            "type": "object",
            "required": ["status", "timestamp", "version"],
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["healthy", "unhealthy", "degraded"],
                    "description": "Overall system health status"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Health check timestamp"
                },
                "version": {
                    "type": "string",
                    "description": "API version",
                    "example": "1.8.1"
                },
                "uptime": {
                    "type": "number",
                    "description": "System uptime in seconds"
                },
                "components": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "enum": ["healthy", "unhealthy"]},
                            "latency": {"type": "number"},
                            "last_check": {"type": "string", "format": "date-time"}
                        }
                    },
                    "description": "Individual component health status"
                },
                "metrics": {
                    "type": "object",
                    "properties": {
                        "requests_per_second": {"type": "number"},
                        "average_latency": {"type": "number"},
                        "error_rate": {"type": "number"}
                    }
                }
            }
        }
    }

def generate_common_responses() -> Dict[str, Any]:
    """Generate common HTTP response definitions"""

    return {
        "BadRequest": {
            "description": "Bad Request - Invalid input parameters",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "type": "https://dt-rag.com/problems/validation-error",
                        "title": "Validation Error",
                        "status": 400,
                        "detail": "Request validation failed",
                        "errors": [
                            {
                                "field": "query",
                                "message": "Field is required",
                                "code": "required"
                            }
                        ],
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
                        "timestamp": "2025-01-14T12:00:00Z"
                    }
                }
            }
        },
        "Unauthorized": {
            "description": "Unauthorized - Authentication credentials are missing or invalid",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "type": "https://dt-rag.com/problems/unauthorized",
                        "title": "Unauthorized",
                        "status": 401,
                        "detail": "Invalid or expired authentication credentials",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174001",
                        "timestamp": "2025-01-14T12:00:00Z"
                    }
                }
            },
            "headers": {
                "WWW-Authenticate": {
                    "schema": {"type": "string"},
                    "description": "Authentication method required",
                    "example": "Bearer realm=\"DT-RAG API\""
                }
            }
        },
        "Forbidden": {
            "description": "Forbidden - Insufficient permissions for the requested operation",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "type": "https://dt-rag.com/problems/forbidden",
                        "title": "Forbidden",
                        "status": 403,
                        "detail": "Insufficient permissions to access this resource",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174002",
                        "timestamp": "2025-01-14T12:00:00Z"
                    }
                }
            }
        },
        "NotFound": {
            "description": "Not Found - The requested resource was not found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "type": "https://dt-rag.com/problems/not-found",
                        "title": "Not Found",
                        "status": 404,
                        "detail": "The requested resource was not found",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174003",
                        "timestamp": "2025-01-14T12:00:00Z"
                    }
                }
            }
        },
        "TooManyRequests": {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "type": "https://dt-rag.com/problems/rate-limit",
                        "title": "Rate Limit Exceeded",
                        "status": 429,
                        "detail": "Request rate limit exceeded. Try again later.",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174004",
                        "timestamp": "2025-01-14T12:00:00Z"
                    }
                }
            },
            "headers": {
                "Retry-After": {
                    "schema": {"type": "integer"},
                    "description": "Seconds to wait before retrying",
                    "example": 60
                },
                "X-RateLimit-Limit": {
                    "schema": {"type": "integer"},
                    "description": "Request limit per time window"
                },
                "X-RateLimit-Remaining": {
                    "schema": {"type": "integer"},
                    "description": "Remaining requests in current window"
                },
                "X-RateLimit-Reset": {
                    "schema": {"type": "integer"},
                    "description": "Unix timestamp when rate limit resets"
                }
            }
        },
        "InternalServerError": {
            "description": "Internal Server Error - An unexpected error occurred",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": {
                        "type": "https://dt-rag.com/problems/internal-error",
                        "title": "Internal Server Error",
                        "status": 500,
                        "detail": "An unexpected error occurred while processing the request",
                        "correlation_id": "123e4567-e89b-12d3-a456-426614174005",
                        "timestamp": "2025-01-14T12:00:00Z"
                    }
                }
            }
        }
    }

def generate_common_parameters() -> Dict[str, Any]:
    """Generate common parameter definitions"""

    return {
        "VersionHeader": {
            "name": "API-Version",
            "in": "header",
            "description": "API version to use for the request",
            "schema": {
                "type": "string",
                "default": "1.8.1",
                "example": "1.8.1"
            }
        },
        "AcceptLanguage": {
            "name": "Accept-Language",
            "in": "header",
            "description": "Preferred language for response content",
            "schema": {
                "type": "string",
                "default": "en-US",
                "example": "en-US"
            }
        },
        "RequestId": {
            "name": "X-Request-ID",
            "in": "header",
            "description": "Client-provided request ID for tracking",
            "schema": {
                "type": "string",
                "format": "uuid"
            }
        },
        "PageParam": {
            "name": "page",
            "in": "query",
            "description": "Page number for pagination (1-based)",
            "schema": {
                "type": "integer",
                "minimum": 1,
                "default": 1,
                "example": 1
            }
        },
        "LimitParam": {
            "name": "limit",
            "in": "query",
            "description": "Number of items per page",
            "schema": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "default": 20,
                "example": 20
            }
        },
        "SortParam": {
            "name": "sort",
            "in": "query",
            "description": "Sort order specification",
            "schema": {
                "type": "string",
                "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*(:asc|:desc)?$",
                "example": "created_at:desc"
            }
        }
    }

def generate_examples() -> Dict[str, Any]:
    """Generate realistic API examples"""

    return {
        "SearchRequestExample": {
            "summary": "Typical search request",
            "description": "A common search request with taxonomy filtering",
            "value": {
                "query": "machine learning algorithms for text classification",
                "taxonomy_filters": [["Technology", "AI", "Machine Learning"]],
                "max_results": 10,
                "search_type": "hybrid",
                "rerank_candidates": 50
            }
        },
        "SearchResponseExample": {
            "summary": "Typical search response",
            "description": "Example search response with ranked results",
            "value": {
                "hits": [
                    {
                        "chunk_id": "doc123_chunk456",
                        "score": 0.89,
                        "text": "Support Vector Machines (SVMs) are powerful supervised learning algorithms...",
                        "source": {
                            "url": "https://example.com/ml-guide",
                            "title": "Machine Learning Algorithms Guide",
                            "date": "2024-01-15"
                        },
                        "taxonomy_path": ["Technology", "AI", "Machine Learning", "Supervised Learning"]
                    }
                ],
                "latency": 0.045,
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_candidates": 50,
                "sources_count": 12,
                "taxonomy_version": "1.8.1"
            }
        },
        "ClassificationExample": {
            "summary": "Document classification request",
            "description": "Example classification request with hint paths",
            "value": {
                "chunk_id": "doc789_chunk123",
                "text": "Deep neural networks have revolutionized computer vision tasks...",
                "hint_paths": [
                    ["Technology", "AI", "Deep Learning"],
                    ["Science", "Computer Science", "Computer Vision"]
                ]
            }
        },
        "PipelineRequestExample": {
            "summary": "RAG pipeline execution request",
            "description": "Complete RAG pipeline request with custom configuration",
            "value": {
                "query": "Explain the differences between supervised and unsupervised learning",
                "taxonomy_version": "1.8.1",
                "search_config": {
                    "max_results": 15,
                    "search_type": "hybrid"
                },
                "generation_config": {
                    "temperature": 0.7,
                    "max_tokens": 800
                }
            }
        }
    }

def generate_api_paths() -> Dict[str, Any]:
    """Generate all API endpoint definitions"""

    paths = {}

    # Health and Status Endpoints
    paths["/health"] = {
        "get": {
            "tags": ["System"],
            "summary": "Health check",
            "description": "Check system health and availability",
            "operationId": "getHealth",
            "security": [],  # Public endpoint
            "responses": {
                "200": {
                    "description": "System is healthy",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/HealthResponse"},
                            "example": {
                                "status": "healthy",
                                "timestamp": "2025-01-14T12:00:00Z",
                                "version": "1.8.1",
                                "uptime": 86400,
                                "components": {
                                    "database": {"status": "healthy", "latency": 0.005},
                                    "search": {"status": "healthy", "latency": 0.012},
                                    "classification": {"status": "healthy", "latency": 0.089}
                                }
                            }
                        }
                    }
                },
                "503": {"$ref": "#/components/responses/InternalServerError"}
            }
        }
    }

    # Authentication Endpoints
    paths["/auth/login"] = {
        "post": {
            "tags": ["Authentication"],
            "summary": "User login",
            "description": "Authenticate user and return access token",
            "operationId": "login",
            "security": [],  # No auth required for login
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/AuthRequest"},
                        "example": {
                            "username": "user@example.com",
                            "password": "SecurePassword123!"
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Login successful",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AuthResponse"}
                        }
                    }
                },
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "429": {"$ref": "#/components/responses/TooManyRequests"}
            }
        }
    }

    # Taxonomy Endpoints
    paths["/taxonomy/versions"] = {
        "get": {
            "tags": ["Taxonomy"],
            "summary": "List taxonomy versions",
            "description": "Retrieve all available taxonomy versions with metadata",
            "operationId": "listTaxonomyVersions",
            "parameters": [
                {"$ref": "#/components/parameters/PageParam"},
                {"$ref": "#/components/parameters/LimitParam"}
            ],
            "responses": {
                "200": {
                    "description": "List of taxonomy versions",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "versions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "version": {"type": "string"},
                                                "created_at": {"type": "string", "format": "date-time"},
                                                "created_by": {"type": "string"},
                                                "change_summary": {"type": "string"},
                                                "node_count": {"type": "integer"}
                                            }
                                        }
                                    },
                                    "pagination": {
                                        "type": "object",
                                        "properties": {
                                            "page": {"type": "integer"},
                                            "limit": {"type": "integer"},
                                            "total": {"type": "integer"},
                                            "has_next": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "500": {"$ref": "#/components/responses/InternalServerError"}
            }
        }
    }

    paths["/taxonomy/{version}/tree"] = {
        "get": {
            "tags": ["Taxonomy"],
            "summary": "Get taxonomy tree",
            "description": "Retrieve complete taxonomy tree for specified version",
            "operationId": "getTaxonomyTree",
            "parameters": [
                {
                    "name": "version",
                    "in": "path",
                    "required": True,
                    "description": "Taxonomy version",
                    "schema": {"type": "string", "example": "1.8.1"}
                },
                {
                    "name": "expand_level",
                    "in": "query",
                    "description": "Tree expansion level (-1 for full tree)",
                    "schema": {"type": "integer", "default": -1}
                }
            ],
            "responses": {
                "200": {
                    "description": "Taxonomy tree structure",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/TaxonomyNode"}
                            }
                        }
                    }
                },
                "404": {"$ref": "#/components/responses/NotFound"},
                "500": {"$ref": "#/components/responses/InternalServerError"}
            }
        }
    }

    # Search Endpoints
    paths["/search"] = {
        "post": {
            "tags": ["Search"],
            "summary": "Search documents",
            "description": "Perform hybrid search using BM25 and vector search with reranking",
            "operationId": "searchDocuments",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/SearchRequest"},
                        "examples": {
                            "basic_search": {"$ref": "#/components/examples/SearchRequestExample"}
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Search results",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/SearchResponse"},
                            "examples": {
                                "search_results": {"$ref": "#/components/examples/SearchResponseExample"}
                            }
                        }
                    },
                    "headers": {
                        "X-Search-Latency": {
                            "schema": {"type": "number"},
                            "description": "Search processing latency in seconds"
                        },
                        "X-Request-ID": {
                            "schema": {"type": "string"},
                            "description": "Request correlation ID"
                        }
                    }
                },
                "400": {"$ref": "#/components/responses/BadRequest"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "429": {"$ref": "#/components/responses/TooManyRequests"},
                "500": {"$ref": "#/components/responses/InternalServerError"}
            }
        }
    }

    # Classification Endpoints
    paths["/classify"] = {
        "post": {
            "tags": ["Classification"],
            "summary": "Classify document chunk",
            "description": "Classify document chunk into taxonomy categories with HITL support",
            "operationId": "classifyDocument",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ClassifyRequest"},
                        "examples": {
                            "classification_request": {"$ref": "#/components/examples/ClassificationExample"}
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Classification result",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ClassifyResponse"}
                        }
                    }
                },
                "400": {"$ref": "#/components/responses/BadRequest"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "429": {"$ref": "#/components/responses/TooManyRequests"},
                "500": {"$ref": "#/components/responses/InternalServerError"}
            }
        }
    }

    # Pipeline Orchestration Endpoints
    paths["/pipeline/execute"] = {
        "post": {
            "tags": ["Orchestration"],
            "summary": "Execute RAG pipeline",
            "description": "Run complete 7-step LangGraph RAG pipeline",
            "operationId": "executePipeline",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/PipelineRequest"},
                        "examples": {
                            "pipeline_request": {"$ref": "#/components/examples/PipelineRequestExample"}
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Pipeline execution result",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PipelineResponse"}
                        }
                    },
                    "headers": {
                        "X-Pipeline-Latency": {
                            "schema": {"type": "number"},
                            "description": "Total pipeline latency in seconds"
                        },
                        "X-Pipeline-Cost": {
                            "schema": {"type": "number"},
                            "description": "Total processing cost in KRW"
                        }
                    }
                },
                "400": {"$ref": "#/components/responses/BadRequest"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "429": {"$ref": "#/components/responses/TooManyRequests"},
                "500": {"$ref": "#/components/responses/InternalServerError"}
            }
        }
    }

    return paths

def save_openapi_spec(spec: Dict[str, Any], output_file: Optional[str] = None):
    """
    Save OpenAPI specification to file

    Args:
        spec: OpenAPI specification dictionary
        output_file: Output file path (optional)
    """

    if output_file is None:
        output_file = Path(__file__).parent / "openapi_spec.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI specification saved to: {output_file}")

def generate_yaml_spec(spec: Dict[str, Any], output_file: Optional[str] = None):
    """
    Generate YAML version of OpenAPI specification

    Args:
        spec: OpenAPI specification dictionary
        output_file: Output YAML file path (optional)
    """

    try:
        import yaml
    except ImportError:
        print("PyYAML not installed. Install with: pip install PyYAML")
        return

    if output_file is None:
        output_file = Path(__file__).parent / "openapi_spec.yaml"

    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(spec, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"OpenAPI YAML specification saved to: {output_file}")

def main():
    """Generate and save OpenAPI specifications"""

    print("Generating OpenAPI 3.0.3 specification for DT-RAG v1.8.1...")

    # Generate specification
    spec = generate_openapi_spec()

    # Save JSON version
    save_openapi_spec(spec)

    # Save YAML version
    generate_yaml_spec(spec)

    # Print summary
    paths_count = len(spec["paths"])
    schemas_count = len(spec["components"]["schemas"])

    print(f"\nOpenAPI specification generated successfully:")
    print(f"- {paths_count} API endpoints")
    print(f"- {schemas_count} data schemas")
    print(f"- {len(spec['tags'])} API categories")
    print(f"- Complete authentication and security definitions")
    print(f"- Comprehensive error handling and examples")

if __name__ == "__main__":
    main()