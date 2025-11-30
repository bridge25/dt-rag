-- Initialize Test Database for Norade
-- Minimal schema for testing (Alembic handles the rest)
--
-- This script only enables extensions required for testing.
-- Full schema is created via Alembic migrations: `alembic upgrade head`

-- Enable pgvector extension (required for vector operations)
CREATE EXTENSION IF NOT EXISTS vector;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Norade Test Database initialized with pgvector extension';
END $$;
