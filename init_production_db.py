"""
Initialize Production Database

Creates all tables required for the API to function.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from apps.api.database import init_database

async def main():
    """Initialize production database"""
    print("=" * 70)
    print("DT-RAG Production Database Initialization")
    print("=" * 70)
    print()

    print("Creating all tables...")
    result = await init_database()

    if result:
        print()
        print("=" * 70)
        print("✅ Database initialized successfully!")
        print("=" * 70)
        print()
        print("Tables created:")
        print("  - taxonomy_nodes")
        print("  - taxonomy_edges")
        print("  - taxonomy_migrations")
        print("  - documents")
        print("  - chunks")
        print("  - embeddings")
        print("  - doc_taxonomy")
        print("  - case_bank")
        print("  - api_keys (from migration 0010)")
        print()
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
