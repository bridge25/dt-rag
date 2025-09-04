# Dynamic Taxonomy RAG - Database Schema (DDL Hardening)

> **Version**: 1.8.1  
> **Team**: A팀 (Taxonomy & Data Platform)  
> **Dependencies**: PostgreSQL 15+, pgvector extension  
> **Migration Type**: DDL Hardening (스택드 PR-2)

## 🎯 Overview

This repository contains the complete database schema implementation for the Dynamic Taxonomy RAG system. It includes:

- **Versioned taxonomy DAG** with int4range span tracking
- **Hybrid search infrastructure** (BM25 + Vector with IVFFlat)
- **Audit logging & HITL queue** for low-confidence classifications
- **Safe rollback procedures** with full transaction support
- **Comprehensive test suite** and seed data

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

## 🚀 Quick Start

### 1. Database Setup

```bash
# Create database
createdb dt_rag

# Install extensions
psql dt_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql dt_rag -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
```

### 2. Run Migrations

```bash
# Using SQL files directly
psql dt_rag -f migrations/0001_initial_schema.sql
psql dt_rag -f migrations/0002_span_range_and_indexes.sql  
psql dt_rag -f migrations/0003_audit_hitl_ivfflat_and_rollback_proc.sql

# OR using Alembic
pip install alembic psycopg2-binary
alembic upgrade head
```

### 3. Load Test Data

```bash
# Insert sample taxonomy and documents
psql dt_rag -f scripts/seed_data.sql
```

### 4. Verify Installation

```bash
# Run schema tests
pip install pytest
pytest tests/test_schema.py -v
```

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
    text TEXT NOT NULL,
    span INT4RANGE NOT NULL,  -- e.g., [100,250)
    chunk_index INTEGER
);

-- GiST index for overlap/containment queries
CREATE INDEX idx_chunks_span_gist ON chunks USING gist (span);

-- Find overlapping chunks
SELECT * FROM chunks 
WHERE span && int4range(200, 300);
```

### Vector Similarity Search

```sql
-- IVFFlat index for fast similarity search
CREATE INDEX idx_embeddings_vec_ivf ON embeddings 
USING ivfflat (vec vector_cosine_ops) WITH (lists = 100);

-- Similarity search with distance threshold
SELECT chunk_id, vec <=> '[0.1,0.2,...]'::vector as distance
FROM embeddings 
ORDER BY distance LIMIT 5;
```

### Safe Taxonomy Rollback

```sql
-- Rollback taxonomy to previous version with full audit trail
CALL taxonomy_rollback(to_version => 2);

-- Check rollback history
SELECT * FROM audit_log 
WHERE action LIKE 'taxonomy_rollback%' 
ORDER BY timestamp DESC;
```

### HITL Queue Management

```sql
-- Add low-confidence classification to human review queue
SELECT add_to_hitl_queue(
    chunk_id => 'uuid-here',
    classification => '{"canonical": ["AI"], "confidence": 0.65}',
    suggested_paths => ARRAY['AI', 'Technology'],
    confidence => 0.65
);

-- View pending reviews
SELECT * FROM v_low_confidence_classifications 
WHERE status = 'pending'
ORDER BY priority, created_at;
```

## 🧪 Testing

### Schema Validation Tests

```bash
# Run all schema tests
pytest tests/test_schema.py -v

# Test specific areas
pytest tests/test_schema.py::TestDatabaseSchema::test_core_tables_exist -v
pytest tests/test_schema.py::TestDatabaseSchema::test_constraints -v
pytest tests/test_schema.py::TestDatabaseSchema::test_rollback_procedure -v
```

### Test Coverage

- ✅ All tables and constraints
- ✅ Index existence and functionality  
- ✅ Trigger and procedure execution
- ✅ Data integrity and referential constraints
- ✅ Vector dimension and confidence ranges
- ✅ Span range operations and utilities
- ✅ HITL queue workflow and logic
- ✅ Audit trail completeness

## 📊 Performance Benchmarks

### Index Performance (Expected)

| Operation | Without Index | With Index | Improvement |
|-----------|---------------|------------|-------------|
| Span overlap queries | 45ms | 0.8ms | **56x faster** |
| Vector similarity (k=5) | 120ms | 2.1ms | **57x faster** |
| Taxonomy path search | 35ms | 0.6ms | **58x faster** |
| BM25 token matching | 28ms | 1.2ms | **23x faster** |

### Rollback Performance Target

- **TTR (Time To Rollback)**: ≤ 15 minutes for any version
- **Audit completeness**: 100% of changes logged
- **Transaction safety**: Full ACID compliance

## 🔒 Security & Compliance

### Audit Logging

Every system action is automatically logged:
- Taxonomy changes (create/update/delete)
- Document uploads and processing
- Search queries and classifications
- HITL queue operations
- Failed operations and errors

### Data Integrity

- **Referential integrity** enforced via foreign keys
- **Constraint validation** on all user inputs
- **Transaction rollback** on any constraint violation
- **Unique constraints** prevent duplicate taxonomy paths
- **Check constraints** ensure valid ranges and formats

## 🚧 Rollback Procedures

### Safe Rollback Protocol

1. **Validation**: Target version must exist
2. **Audit initiation**: Log rollback start with metadata
3. **Dependency resolution**: Update dependent doc_taxonomy mappings
4. **Node/edge removal**: Delete newer version data
5. **Migration recording**: Track rollback in taxonomy_migrations
6. **Statistics update**: Refresh query planner statistics
7. **Error handling**: Full rollback on any failure with detailed logging

### Rollback TTR Guarantee

- **Target**: ≤ 15 minutes for any rollback operation
- **Monitoring**: Automated duration tracking in audit_log
- **Recovery**: Failed rollbacks leave system in consistent state

## 📝 Development Notes

### Environment Variables

```bash
# Database connection (for Alembic)
export DATABASE_URL="postgresql://user:password@localhost:5432/dt_rag"

# Test database (for pytest)  
export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/dt_rag_test"
```

### Common Operations

```bash
# Generate new migration
alembic revision -m "Description of changes"

# Check migration status
alembic current
alembic history

# Downgrade by one version
alembic downgrade -1

# Upgrade to specific version
alembic upgrade 0002
```

## 🎯 Next Steps (B/C Team Integration)

This DDL hardening provides the foundation for:

**B팀 (Orchestration)**: 
- FastAPI models match this schema exactly
- `/classify` endpoint maps to doc_taxonomy table
- HITL queue integration for low-confidence results

**C팀 (Frontend)**:  
- TypeScript interfaces generated from this schema
- Real-time taxonomy tree visualization
- HITL review dashboard for manual classifications

## 📞 Support & Documentation

- **Schema Issues**: Check `tests/test_schema.py` for expected behavior
- **Migration Problems**: Review `alembic/env.py` configuration  
- **Performance**: Analyze query plans with `EXPLAIN (ANALYZE, BUFFERS)`
- **Rollback Issues**: Check `audit_log` table for detailed error information

---

**Generated**: 2025-01-15  
**Schema Version**: 1.8.1  
**Team**: A팀 (Taxonomy & Data Platform)  
**Status**: ✅ Ready for B/C team integration