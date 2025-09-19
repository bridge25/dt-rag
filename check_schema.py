#!/usr/bin/env python3
"""
Check database table schema
"""

import asyncio
import sys
import os

# Add project root path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def check_schema():
    """Check database table schemas"""
    from database import db_manager
    from sqlalchemy import text

    async with db_manager.async_session() as session:
        print("=== Database Schema Information ===")

        # Check documents table
        result = await session.execute(text('PRAGMA table_info(documents)'))
        print('\nDocuments table schema:')
        for row in result.fetchall():
            print(f'  {row}')

        # Check chunks table
        result = await session.execute(text('PRAGMA table_info(chunks)'))
        print('\nChunks table schema:')
        for row in result.fetchall():
            print(f'  {row}')

        # Check embeddings table
        result = await session.execute(text('PRAGMA table_info(embeddings)'))
        print('\nEmbeddings table schema:')
        for row in result.fetchall():
            print(f'  {row}')

        # Check doc_taxonomy table
        result = await session.execute(text('PRAGMA table_info(doc_taxonomy)'))
        print('\nDoc_taxonomy table schema:')
        for row in result.fetchall():
            print(f'  {row}')

if __name__ == "__main__":
    asyncio.run(check_schema())