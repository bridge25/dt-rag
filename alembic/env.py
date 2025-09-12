"""Alembic environment configuration for Dynamic Taxonomy RAG v1.8.1"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Note: This project uses raw SQL migrations instead of SQLAlchemy models
# No SQLAlchemy Base model is available in common_schemas.models (Pydantic only)
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_database_url():
    """Get database URL from environment or config."""
    # Priority: environment variable > config file
    return os.getenv('DATABASE_URL') or config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Enable PostgreSQL-specific features
        render_as_batch=False,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Override URL from environment if available
    config_dict = config.get_section(config.config_ini_section)
    config_dict['sqlalchemy.url'] = get_database_url()
    
    connectable = engine_from_config(
        config_dict,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # PostgreSQL-specific configuration
            render_as_batch=False,
            compare_type=True,
            compare_server_default=True,
            # Include schemas in autogenerate
            include_schemas=True,
            # Custom naming convention for constraints
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()

def render_item(type_, obj, autogen_context):
    """Apply custom rendering for certain schema items."""
    if type_ == "index" and obj.name:
        # Preserve index names
        return f'op.create_index("{obj.name}", "{obj.table.name}", {[col.name for col in obj.columns]!r})'
    return False

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()