"""Enhanced Alembic environment configuration for CI/CD compatibility"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from alembic import context
import os
import sys
import time
from typing import Optional

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models for metadata
try:
    from apps.api.database import Base
    target_metadata = Base.metadata
except ImportError as e:
    print(f"Warning: Could not import models: {e}")
    target_metadata = None

def get_database_url() -> str:
    """Get database URL with environment variable priority."""
    # Priority: environment variable > config file
    url = os.getenv('DATABASE_URL') or config.get_main_option("sqlalchemy.url")
    
    # Convert async URLs to sync for Alembic
    if url and "sqlite+aiosqlite" in url:
        url = url.replace("sqlite+aiosqlite", "sqlite")
    elif url and "postgresql+asyncpg" in url:
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    
    return url

def wait_for_database(url: str, max_attempts: int = 30, delay: float = 1.0) -> bool:
    """Wait for database to be ready with retry logic."""
    from sqlalchemy import create_engine
    
    print(f"Waiting for database to be ready... (max {max_attempts} attempts)")
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Create a temporary engine for testing
            test_engine = create_engine(url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                # Simple test query
                if 'postgresql' in url:
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute(text("SELECT 1"))
                print(f"✅ Database connection successful on attempt {attempt}")
                test_engine.dispose()
                return True
        except (OperationalError, ProgrammingError) as e:
            print(f"⏳ Attempt {attempt}/{max_attempts} failed: {str(e)[:100]}...")
            if attempt < max_attempts:
                time.sleep(delay)
            test_engine.dispose() if 'test_engine' in locals() else None
    
    print(f"❌ Database not ready after {max_attempts} attempts")
    return False

def ensure_extensions(connection) -> None:
    """Ensure required PostgreSQL extensions are available."""
    database_url = get_database_url()
    if database_url and 'postgresql' in database_url:
        try:
            # Check if pgvector extension is available
            result = connection.execute(text(
                "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
            ))
            if result.fetchone():
                print("✅ pgvector extension is available")
                # Create extension if not exists
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                connection.commit()
                print("✅ pgvector extension enabled")
            else:
                print("⚠️ pgvector extension not available, but continuing...")
        except Exception as e:
            print(f"⚠️ Extension check failed: {e}, but continuing...")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=False,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def render_item(type_, obj, autogen_context):
    """Custom rendering for special database items."""
    # Custom handling for PostgreSQL-specific types and constraints
    if type_ == "type" and hasattr(obj, 'name'):
        # Handle vector types gracefully
        if 'vector' in str(obj).lower():
            return f"postgresql.{obj}"
    return False

def run_migrations_online() -> None:
    """Run migrations in 'online' mode with enhanced error handling."""
    configuration = config.get_section(config.config_ini_section)
    
    # Get database URL
    url = get_database_url()
    if not url:
        raise ValueError("No database URL found in environment or config")
    
    configuration["sqlalchemy.url"] = url
    
    # Wait for database to be ready (especially important in CI)
    if not wait_for_database(url):
        raise RuntimeError("Database is not ready for migrations")
    
    # Enhanced engine configuration for CI/CD stability
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Disable connection pooling for migrations
        pool_pre_ping=True,       # Verify connections before use
        pool_recycle=300,         # Recycle connections every 5 minutes
        echo=os.getenv('ALEMBIC_ECHO', 'false').lower() == 'true'  # Optional SQL logging
    )

    with connectable.connect() as connection:
        # Ensure required extensions
        ensure_extensions(connection)
        
        # Configure Alembic context
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=False,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            render_item=render_item,
            # Transaction configuration for stability
            transaction_per_migration=True,
            transactional_ddl=True,
        )

        # Run migrations within a transaction
        try:
            with context.begin_transaction():
                context.run_migrations()
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            # In CI, we might want to continue with degraded functionality
            if os.getenv('CI') == 'true':
                print("⚠️ Running in CI mode - attempting graceful handling...")
                # Could implement fallback logic here
            raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
