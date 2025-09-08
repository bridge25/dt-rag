# RAG System Documentation

## Overview
This is a sample markdown document for testing the RAG (Retrieval-Augmented Generation) taxonomy system.

## Key Concepts
- **Document Ingestion**: Processing and indexing documents
- **Taxonomy Classification**: Automatic categorization of content
- **Vector Search**: Semantic search capabilities
- **HITL (Human-in-the-Loop)**: Manual review for low-confidence classifications

## Sample Content
RAG systems combine retrieval and generation to provide accurate, contextual responses. The taxonomy system helps organize and classify documents for better retrieval accuracy.

### Technical Specifications
- Chunk size: 500 characters with 128 character overlap
- Confidence threshold: 0.70 for HITL queue
- Vector dimensions: 384 (sentence-transformers)
- BM25 + Vector hybrid search

## Expected Classification
This document should be classified under:
- Primary: ["AI", "RAG"]  
- Secondary: ["Documentation", "Technical"]
- Confidence: Should be > 0.80 for clear RAG content