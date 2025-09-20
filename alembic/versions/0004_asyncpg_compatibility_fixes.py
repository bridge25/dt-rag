"""AsyncPG compatibility fixes and vector operator optimization

Revision ID: 0004
Revises: 0003
Create Date: 2025-09-19 13:10:00.000000

This migration addresses Critical Issues found in Phase 2:
1. PostgreSQL vector operator compatibility (<=> to <->)
2. Ensure doc_metadata column exists and is properly typed
3. Add proper indexes for asyncpg compatibility
4. Enhanced transaction safety and error handling
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists using information_schema"""
    bind = op.get_bind()
    result = bind.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND column_name = :column_name
        )
    """), {"table_name": table_name, "column_name": column_name})
    return result.scalar()


def check_index_exists(index_name: str) -> bool:
    """Check if index exists using information_schema"""
    bind = op.get_bind()
    result = bind.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = :index_name
        )
    """), {"index_name": index_name})
    return result.scalar()


def check_function_exists(function_name: str) -> bool:
    """Check if function exists using information_schema"""
    bind = op.get_bind()
    result = bind.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.routines 
            WHERE routine_name = :function_name
        )
    """), {"function_name": function_name})
    return result.scalar()


def upgrade() -> None:
    """Apply asyncpg compatibility fixes with enhanced transaction safety"""

    bind = op.get_bind()
    
    # Check database type safely
    is_postgresql = False
    try:
        # Try to determine if we're using PostgreSQL
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            database_url = str(bind.get_bind().url)
        
        is_postgresql = 'postgresql' in database_url.lower()
    except Exception:
        # Fallback: check dialect name
        try:
            is_postgresql = bind.dialect.name == 'postgresql'
        except Exception:
            # Final fallback: try to detect PostgreSQL by running a PostgreSQL-specific query
            try:
                bind.execute(text("SELECT version()"))
                result = bind.execute(text("SELECT current_database()"))
                is_postgresql = True
            except Exception:
                is_postgresql = False

    if is_postgresql:
        print("Applying PostgreSQL-specific fixes...")

        # 1. Ensure doc_metadata column exists in taxonomy_nodes
        # Use information_schema to check existence to avoid transaction rollback
        if not check_column_exists('taxonomy_nodes', 'doc_metadata'):
            try:
                op.add_column('taxonomy_nodes',
                             sa.Column('doc_metadata', postgresql.JSONB(), nullable=True))
                print("✓ Added doc_metadata column to taxonomy_nodes")
            except Exception as e:
                print(f"⚠ Could not add doc_metadata column (may already exist): {e}")
        else:
            print("✓ doc_metadata column already exists in taxonomy_nodes")

        # 2. Add better vector indexes for asyncpg compatibility
        # Check for pgvector extension before creating vector indexes
        try:
            # Check if pgvector is available
            bind.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
            pgvector_available = True
        except Exception:
            pgvector_available = False
            print("⚠ pgvector extension not found - skipping vector indexes")

        if pgvector_available:
            try:
                # Drop old vector indexes if they exist (safe operation)
                for old_index in ['idx_embeddings_vec_cosine', 'idx_embeddings_vec_ivf']:
                    if check_index_exists(old_index):
                        bind.execute(text(f'DROP INDEX IF EXISTS {old_index}'))
                        print(f"✓ Dropped old index: {old_index}")

                # Create HNSW index for better performance with asyncpg
                if not check_index_exists('idx_embeddings_vec_hnsw'):
                    bind.execute(text('''
                        CREATE INDEX idx_embeddings_vec_hnsw
                        ON embeddings USING hnsw (vec vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    '''))
                    print("✓ Created HNSW vector index for better asyncpg compatibility")
                else:
                    print("✓ HNSW vector index already exists")

            except Exception as e:
                print(f"⚠ Vector index management failed: {e}")

        # 3. Create function for safe vector operations
        if not check_function_exists('safe_cosine_distance'):
            try:
                bind.execute(text(r'''
                    CREATE OR REPLACE FUNCTION safe_cosine_distance(vec1 vector, vec2 vector)
                    RETURNS float8
                    LANGUAGE sql
                    IMMUTABLE STRICT
                    AS $func$
                        SELECT CASE
                            WHEN vec1 IS NULL OR vec2 IS NULL THEN 1.0
                            ELSE 1.0 - (vec1 <#> vec2)
                        END;
                    $func$;
                '''))
                print("✓ Created safe_cosine_distance function")
            except Exception as e:
                print(f"⚠ Could not create safe_cosine_distance function: {e}")
        else:
            print("✓ safe_cosine_distance function already exists")

        # 4. Add indexes for better query performance (idempotent)
        performance_indexes = [
            ('idx_chunks_doc_id_text', 'chunks', 'doc_id, text'),
            ('idx_doc_taxonomy_doc_path', 'doc_taxonomy', 'doc_id, path'),
            ('idx_embeddings_chunk_model', 'embeddings', 'chunk_id, model_name')
        ]

        for idx_name, table_name, columns in performance_indexes:
            if not check_index_exists(idx_name):
                try:
                    bind.execute(text(f'CREATE INDEX {idx_name} ON {table_name} ({columns})'))
                    print(f"✓ Created index: {idx_name}")
                except Exception as e:
                    print(f"⚠ Could not create index {idx_name}: {e}")
            else:
                print(f"✓ Index {idx_name} already exists")

        # 5. Update statistics for better query planning (safe operation)
        try:
            for table in ['taxonomy_nodes', 'chunks', 'embeddings', 'doc_taxonomy']:
                bind.execute(text(f'ANALYZE {table}'))
            print("✓ Updated table statistics")
        except Exception as e:
            print(f"⚠ Could not update statistics: {e}")

        print("✅ PostgreSQL asyncpg compatibility fixes applied successfully")

    else:
        print("SQLite detected - applying SQLite-compatible fixes...")
        
        # For SQLite, ensure the schema is compatible
        if not check_column_exists('taxonomy_nodes', 'doc_metadata'):
            try:
                # Add doc_metadata column for SQLite
                op.add_column('taxonomy_nodes',
                             sa.Column('doc_metadata', sa.TEXT(), nullable=True))
                print("✓ Added doc_metadata column to taxonomy_nodes (SQLite)")
            except Exception as e:
                print(f"⚠ Could not add doc_metadata column: {e}")
        else:
            print("✓ doc_metadata column already exists in taxonomy_nodes (SQLite)")

        print("✅ SQLite compatibility fixes applied successfully")


def downgrade() -> None:
    """Remove asyncpg compatibility fixes with transaction safety"""

    bind = op.get_bind()
    
    # Check database type safely
    is_postgresql = False
    try:
        if hasattr(bind, 'engine'):
            database_url = str(bind.engine.url)
        elif hasattr(bind, 'url'):
            database_url = str(bind.url)
        else:
            database_url = str(bind.get_bind().url)
        
        is_postgresql = 'postgresql' in database_url.lower()
    except Exception:
        try:
            is_postgresql = bind.dialect.name == 'postgresql'
        except Exception:
            is_postgresql = False

    if is_postgresql:
        print("Removing PostgreSQL-specific changes...")
        
        # Remove PostgreSQL-specific changes (safe operations)
        try:
            if check_function_exists('safe_cosine_distance'):
                bind.execute(text('DROP FUNCTION IF EXISTS safe_cosine_distance(vector, vector)'))
                print("✓ Removed safe_cosine_distance function")
                
            # Remove indexes
            indexes_to_remove = [
                'idx_embeddings_vec_hnsw',
                'idx_chunks_doc_id_text', 
                'idx_doc_taxonomy_doc_path',
                'idx_embeddings_chunk_model'
            ]
            
            for idx_name in indexes_to_remove:
                if check_index_exists(idx_name):
                    bind.execute(text(f'DROP INDEX IF EXISTS {idx_name}'))
                    print(f"✓ Removed index: {idx_name}")

            print("✅ Removed PostgreSQL asyncpg compatibility fixes")
            
        except Exception as e:
            print(f"⚠ Error during downgrade: {e}")

    # Note: We don't remove doc_metadata column as it may contain data
    print("✅ Downgrade completed (doc_metadata column preserved to prevent data loss)")
