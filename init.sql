-- Initialize DT-RAG database with pgvector extension and required tables

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table for storing document content and metadata
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(768),  -- Using 768 dimensions for text embeddings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx ON documents
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create taxonomy table for dynamic classification
CREATE TABLE IF NOT EXISTS taxonomy (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES taxonomy(id),
    level INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document_taxonomy junction table
CREATE TABLE IF NOT EXISTS document_taxonomy (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    taxonomy_id INTEGER REFERENCES taxonomy(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (document_id, taxonomy_id)
);

-- Create search_logs table for RAGAS evaluation
CREATE TABLE IF NOT EXISTS search_logs (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    response TEXT,
    retrieved_docs JSONB,
    context_precision FLOAT,
    context_recall FLOAT,
    faithfulness FLOAT,
    answer_relevancy FLOAT,
    search_type VARCHAR(50) DEFAULT 'hybrid',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample taxonomy data
INSERT INTO taxonomy (name, description, level) VALUES
('Technology', 'Technology related content', 0),
('Science', 'Science related content', 0),
('Business', 'Business related content', 0),
('AI/ML', 'Artificial Intelligence and Machine Learning', 1),
('Software', 'Software development and programming', 1),
('Data Science', 'Data analysis and statistics', 1)
ON CONFLICT (name) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample documents for testing
INSERT INTO documents (title, content, metadata) VALUES
(
    'DT-RAG System Overview',
    'Dynamic Taxonomy RAG (DT-RAG) is an advanced retrieval-augmented generation system that combines vector search with dynamic document classification. It uses pgvector for efficient similarity search and supports hybrid search combining BM25 and vector search.',
    '{type: documentation, category: system}'
),
(
    'Vector Embeddings Guide',
    'Vector embeddings are numerical representations of text that capture semantic meaning. In DT-RAG, we use 768-dimensional embeddings generated from transformer models to enable semantic search capabilities.',
    '{type: guide, category: technical}'
),
(
    'RAGAS Evaluation Metrics',
    'RAGAS (RAG Assessment) provides comprehensive evaluation metrics for RAG systems including Context Precision, Context Recall, Faithfulness, and Answer Relevancy. These metrics help assess the quality and reliability of retrieval-augmented generation systems.',
    '{type: documentation, category: evaluation}'
)
ON CONFLICT DO NOTHING;

-- Create full-text search index
CREATE INDEX IF NOT EXISTS documents_content_fts_idx ON documents
USING gin(to_tsvector('english', content || ' ' || title));

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_search_logs_created_at ON search_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_taxonomy_parent_id ON taxonomy(parent_id);

COMMENT ON TABLE documents IS 'Stores document content with vector embeddings for semantic search';
COMMENT ON TABLE taxonomy IS 'Hierarchical taxonomy for dynamic document classification';
COMMENT ON TABLE search_logs IS 'Logs search queries and responses for RAGAS evaluation';
