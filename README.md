# Dynamic Taxonomy RAG System

> **Version**: 1.8.1
> **Team**: A팀 (Taxonomy & Data Platform)
> **Status**: ✅ Ready for B/C team integration

A production-ready RAG (Retrieval-Augmented Generation) system with dynamic taxonomy classification, advanced document processing, and comprehensive orchestration capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ with pgvector extension

### 🔌 Staging 접속 좌표 & 🧪 Quick Smoke

![staging-smoke](https://github.com/bridge25/Unmanned/actions/workflows/staging-smoke.yml/badge.svg)

#### 🌐 Environment Setup
- **Local**: BASE_URL=`http://localhost:8000`
- **Remote**: BASE_URL=`https://api.staging.example.com` (Repo Variables: `STAGING_API_BASE`)
- **Full Guide**: [ACCESS_CARD](dt-rag/docs/bridge/ACCESS_CARD.md)

#### 🧪 Smoke Testing
```bash
STAGING_API_BASE=... API_KEY=... ./dt-rag/scripts/smoke.sh
```

### Installation
```bash
# Clone the repository
git clone https://github.com/your-org/dt-rag.git
cd dt-rag

# Database Setup
createdb dt_rag
psql dt_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql dt_rag -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"

# Install Python dependencies
pip install -e packages/common-schemas/

# Install Node.js dependencies
cd apps/frontend-admin
npm install

# Run Database Migrations
psql dt_rag -f migrations/0001_initial_schema.sql
psql dt_rag -f migrations/0002_span_range_and_indexes.sql
psql dt_rag -f migrations/0003_audit_hitl_ivfflat_and_rollback_proc.sql

# Load Test Data
psql dt_rag -f scripts/seed_data.sql
```

### 4. Verify Installation
```bash
# Run schema tests
pip install pytest
pytest tests/test_schema.py -v
```

## 🏗️ System Architecture

### Core Components

#### A-team: Database & API (PostgreSQL + FastAPI)
- **Location**: `apps/database/` and `apps/api/`
- **Features**:
  - PostgreSQL with advanced indexing
  - FastAPI with OpenAPI v1.8.1 spec
  - Dynamic taxonomy management
  - High-performance document classification
- **Status**: ✅ Production Ready (98%)

#### B-team: Orchestration (Task Management)
- **Location**: `apps/orchestration/`
- **Features**:
  - LangGraph 7-step RAG pipeline
  - Agent Factory system
  - CBR (Case-Based Reasoning)
  - MCP tool integration
- **Status**: ✅ Ready for Integration

#### C-team: Frontend & Administration
- **Location**: `apps/frontend-admin/`
- **Features**:
  - React TypeScript interface
  - Tree-based taxonomy visualization
  - Real-time monitoring dashboard
  - HITL classification interface
- **Status**: 🚧 In Development

### 📋 Test Resources
- **Test Data**: [minimal seeds](dt-rag/docs/seeds/minimal/EXPECTED.md)
- **Expected Results**: Version 1.8.1 baseline
- **CI/CD**: Automated testing on PR/push

## 📊 Database Architecture

### Core Tables

| Table | Purpose | Key Features |
|-------|---------|-------------|
| `taxonomy_nodes` | DAG node definitions | Versioned paths, canonical hierarchy |
| `taxonomy_edges` | Parent-child relationships | Version-aware, cycle prevention |
| `documents` | Source documents | Metadata, checksums, content types |
| `chunks` | Text segments | **int4range spans**, character positions |
| `embeddings` | Vector storage | **vector(1536)**, BM25 tokens |
| `doc_taxonomy` | Document classifications | Confidence scoring, multi-source |
| `audit_log` | System activity tracking | Comprehensive audit trail |
| `hitl_queue` | Human review queue | Low confidence (<0.7) classifications |

### Advanced Features

- **GiST Indexes** for int4range overlap/containment queries
- **IVFFlat Vector Index** (lists=100) for similarity search
- **GIN Indexes** for array path searches and BM25 tokens
- **Automated Audit Triggers** for all taxonomy changes
- **Rollback Procedures** with full transaction safety
- **Utility Functions** for span operations and path management

## 📋 Migration Files

### SQL Migrations (`migrations/`)

1. **`0001_initial_schema.sql`** - Core tables with constraints
   - taxonomy_nodes, taxonomy_edges, taxonomy_migrations
   - documents, chunks, embeddings, doc_taxonomy
   - Basic indexes and foreign keys

2. **`0002_span_range_and_indexes.sql`** - Performance optimization
   - GiST indexes for int4range operations
   - GIN indexes for array searches
   - Utility functions (span_length, spans_overlap, taxonomy_depth)
   - Expression and partial indexes

3. **`0003_audit_hitl_ivfflat_and_rollback_proc.sql`** - Production features
   - audit_log table with comprehensive tracking
   - hitl_queue for human-in-the-loop reviews
   - IVFFlat vector index (lists=100)
   - taxonomy_rollback procedure with transaction safety
   - Automated audit triggers

### Alembic Migrations (`alembic/versions/`)

- **`0001_initial_schema.py`** - Executes SQL file 0001
- **`0002_span_range_and_indexes.py`** - Executes SQL file 0002
- **`0003_audit_hitl_ivfflat_and_rollback_proc.py`** - Executes SQL file 0003

## 🔧 Key Features

### int4range Span Tracking

```sql
-- Character positions in original documents
CREATE TABLE chunks (
    chunk_id UUID PRIMARY KEY,
    doc_id UUID NOT NULL,
    chunk_text TEXT NOT NULL,
    start_byte INT4 NOT NULL,
    end_byte INT4 NOT NULL,
    char_span int4range GENERATED ALWAYS AS (int4range(start_byte, end_byte, '[)')) STORED
);

-- GiST index for overlap queries
CREATE INDEX idx_chunks_char_span_gist ON chunks USING GIST (char_span);
```

### Vector Similarity Search

```sql
-- High-performance vector storage
CREATE TABLE embeddings (
    chunk_id UUID PRIMARY KEY,
    embedding vector(1536) NOT NULL,
    bm25_tokens TEXT[] DEFAULT '{}'
);

-- IVFFlat index for similarity search
CREATE INDEX idx_embeddings_ivfflat ON embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- GIN index for BM25 token search
CREATE INDEX idx_embeddings_bm25_gin ON embeddings USING GIN (bm25_tokens);
```

### Dynamic Taxonomy with Versioning

```sql
-- Versioned taxonomy nodes
CREATE TABLE taxonomy_nodes (
    node_id UUID PRIMARY KEY,
    canonical_path TEXT[] NOT NULL,
    node_name TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT '1.0.0',
    description TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Version-aware edges
CREATE TABLE taxonomy_edges (
    edge_id UUID PRIMARY KEY,
    parent_node_id UUID REFERENCES taxonomy_nodes(node_id),
    child_node_id UUID REFERENCES taxonomy_nodes(node_id),
    version TEXT NOT NULL,
    edge_type TEXT DEFAULT 'parent_child'
);
```

### Safe Rollback Procedures

```sql
-- Transaction-safe rollback with comprehensive audit
CREATE OR REPLACE FUNCTION taxonomy_rollback(target_version TEXT)
RETURNS TABLE(operation TEXT, affected_rows INT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Detailed rollback implementation with audit logging
    -- Full transaction safety and integrity checks
    RETURN QUERY
    SELECT 'nodes_deactivated'::TEXT, count(*)::INT
    FROM taxonomy_nodes
    WHERE version > target_version;
END;
$$;
```

## 🧪 Development Guide

### Testing
```bash
# Unit tests
pytest tests/

# Integration tests
pytest tests/integration/

# Schema validation
pytest tests/test_schema.py

# Performance benchmarks
pytest tests/test_performance.py
```

### Local Development
```bash
# Start development environment
docker-compose up -d

# Run API server
cd apps/api
uvicorn main:app --reload

# Run frontend
cd apps/frontend-admin
npm run dev
```

### Code Quality
```bash
# Linting
flake8 apps/ packages/
eslint apps/frontend-admin/src/

# Type checking
mypy apps/api/
npm run type-check
```

## 📈 Monitoring & Observability

### Health Checks
- **API Health**: `GET /health`
- **Database Health**: Connection and query performance
- **Search Performance**: Latency and accuracy metrics

### Metrics Collection
- Response times (p50, p95, p99)
- Classification accuracy
- Search relevance scores
- System resource utilization

### Alerting
- High error rates (>5%)
- Slow response times (>2s p95)
- Database connection issues
- Low confidence classifications (>30%)

## 🔒 Security & Compliance

### Authentication & Authorization
- JWT-based API authentication
- Role-based access control (RBAC)
- API key management for service accounts

### Data Protection
- PII detection and masking
- Audit logging for all operations
- Encryption at rest and in transit
- GDPR/CCPA compliance features

### Security Headers
- CORS configuration
- Rate limiting
- Input validation and sanitization
- SQL injection prevention

## 🚀 Deployment & Operations

### Docker Deployment
```bash
# Build images
docker-compose build

# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Configuration
```bash
# Required environment variables
DATABASE_URL=postgresql://user:pass@localhost:5432/dt_rag
OPENAI_API_KEY=sk-your-key-here
STAGING_API_BASE=https://api.staging.example.com
```

### Backup & Recovery
```bash
# Database backup
pg_dump dt_rag > backup_$(date +%Y%m%d).sql

# Restore from backup
psql dt_rag < backup_20231201.sql
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write comprehensive tests
- Document all public APIs
- Follow semantic versioning

### Issue Reporting
- Use GitHub Issues for bug reports
- Provide detailed reproduction steps
- Include relevant logs and error messages
- Specify environment details

## 📞 Support & Documentation

### Getting Help
- **Documentation**: [Full API Documentation](docs/api/)
- **Examples**: [Usage Examples](examples/)
- **FAQ**: [Frequently Asked Questions](docs/faq.md)

### Team Contacts
- **A-team (Database/API)**: database-team@company.com
- **B-team (Orchestration)**: orchestration-team@company.com
- **C-team (Frontend)**: frontend-team@company.com

**문제 발생시**: GitHub Issues 또는 각 팀 담당자에게 연락

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT and embedding models
- PostgreSQL community for pgvector extension
- FastAPI team for the excellent web framework
- React and TypeScript communities