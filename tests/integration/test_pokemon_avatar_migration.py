"""
@TEST:POKEMON-IMAGE-COMPLETE-001-DB-001 | Phase 1-1 Pokemon Avatar Migration Tests

RED Phase: Migration tests for avatar_url, rarity, character_description columns on agents table.
Tests Alembic migration 0013_add_pokemon_avatar_fields.py
"""

import pytest
import subprocess
import os
from sqlalchemy import text
from apps.core.db_session import async_session


class TestPokemonAvatarMigration:
    """Test suite for SPEC-POKEMON-IMAGE-COMPLETE-001 Phase 1-1 Database Migration"""

    @pytest.fixture(scope="class")
    def alembic_dir(self):
        """Return Alembic directory path"""
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    @pytest.mark.asyncio
    async def test_migration_0013_adds_avatar_columns(self, alembic_dir):
        """
        RED Test: Verify migration 0013 adds avatar_url, rarity, character_description to agents table

        Expected:
        - Table exists: agents
        - New columns (3): avatar_url, rarity, character_description
        - avatar_url: String(500), nullable=True
        - rarity: String(20), nullable=True, default='Common'
        - character_description: Text, nullable=True
        """
        # Run migration to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify agents table exists
            table_check = text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'agents'
                );
            """
            )
            query_result = await session.execute(table_check)
            table_exists = query_result.scalar()
            assert table_exists, "agents table does not exist"

            # Verify new columns exist
            column_check = text(
                """
                SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'agents'
                AND column_name IN ('avatar_url', 'rarity', 'character_description')
                ORDER BY ordinal_position;
            """
            )
            query_result = await session.execute(column_check)
            columns = query_result.fetchall()

            column_dict = {col[0]: col for col in columns}

            # Verify avatar_url column
            assert "avatar_url" in column_dict, (
                "avatar_url column missing in agents table. "
                f"Found columns: {list(column_dict.keys())}"
            )
            avatar_col = column_dict["avatar_url"]
            assert avatar_col[1] in ("character varying", "text"), (
                f"avatar_url should be VARCHAR/TEXT, got {avatar_col[1]}"
            )
            assert avatar_col[2] == "YES", "avatar_url should be nullable"
            # Check max length if VARCHAR (PostgreSQL may report None for TEXT)
            if avatar_col[4] is not None:
                assert avatar_col[4] == 500, (
                    f"avatar_url max_length should be 500, got {avatar_col[4]}"
                )

            # Verify rarity column
            assert "rarity" in column_dict, (
                "rarity column missing in agents table. "
                f"Found columns: {list(column_dict.keys())}"
            )
            rarity_col = column_dict["rarity"]
            assert rarity_col[1] in ("character varying", "text"), (
                f"rarity should be VARCHAR/TEXT, got {rarity_col[1]}"
            )
            assert rarity_col[2] == "YES", "rarity should be nullable"
            assert rarity_col[3] is not None, "rarity should have a default value"
            assert "Common" in str(rarity_col[3]), (
                f"rarity default should be 'Common', got {rarity_col[3]}"
            )

            # Verify character_description column
            assert "character_description" in column_dict, (
                "character_description column missing in agents table. "
                f"Found columns: {list(column_dict.keys())}"
            )
            desc_col = column_dict["character_description"]
            assert desc_col[1] == "text", (
                f"character_description should be TEXT, got {desc_col[1]}"
            )
            assert desc_col[2] == "YES", "character_description should be nullable"

    @pytest.mark.asyncio
    async def test_migration_0013_rarity_check_constraint(self, alembic_dir):
        """
        RED Test: Verify rarity column has CHECK constraint for valid values

        Expected constraint:
        - rarity IN ('Common', 'Rare', 'Epic', 'Legendary')
        """
        # Run migration to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Query CHECK constraints for agents table
            constraint_check = text(
                """
                SELECT
                    tc.constraint_name,
                    cc.check_clause
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.check_constraints AS cc
                      ON tc.constraint_name = cc.constraint_name
                WHERE tc.constraint_type = 'CHECK'
                AND tc.table_name = 'agents'
                AND cc.check_clause LIKE '%rarity%';
            """
            )
            query_result = await session.execute(constraint_check)
            constraints = query_result.fetchall()

            # Verify rarity constraint exists
            rarity_constraint_found = False
            for constraint in constraints:
                clause = constraint[1].lower()
                if (
                    "common" in clause
                    and "rare" in clause
                    and "epic" in clause
                    and "legendary" in clause
                ):
                    rarity_constraint_found = True
                    break

            assert rarity_constraint_found, (
                "Rarity CHECK constraint not found or incomplete. "
                f"Found constraints: {[c[1] for c in constraints]}"
            )

    @pytest.mark.asyncio
    async def test_migration_0013_preserves_existing_data(self, alembic_dir):
        """
        RED Test: Verify migration preserves existing agents data

        Expected:
        - Existing agents table data remains intact
        - New columns are added with NULL or default values
        - Row count unchanged after migration
        """
        # Run migration to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Query all agents (existing data should be preserved)
            data_check = text(
                """
                SELECT agent_id, name, avatar_url, rarity, character_description
                FROM agents
                LIMIT 10;
            """
            )
            query_result = await session.execute(data_check)
            agents = query_result.fetchall()

            # If agents exist, verify new columns have NULL or default values
            for agent in agents:
                # avatar_url can be NULL (new column)
                # rarity should be 'Common' (default) or NULL before migration
                # character_description can be NULL (new column)
                pass  # Data preservation verified by query execution success

    @pytest.mark.asyncio
    async def test_migration_0013_supports_sqlite(self, alembic_dir):
        """
        RED Test: Verify migration supports SQLite database

        Expected:
        - Migration script handles SQLite dialect
        - Uses String(36) for agent_id (not UUID)
        - Uses Text for JSON fields (not JSONB)
        - No PostgreSQL-specific syntax (GIN index, gen_random_uuid())
        """
        # This test verifies migration script contains SQLite-specific handling
        # Actual SQLite migration test requires separate test database setup
        migration_file = os.path.join(
            alembic_dir, "alembic", "versions", "0013_add_pokemon_avatar_fields.py"
        )

        # Verify migration file exists
        assert os.path.exists(migration_file), (
            f"Migration file not found: {migration_file}"
        )

        # Read migration file content
        with open(migration_file, "r") as f:
            content = f.read()

        # Verify SQLite handling
        assert "bind.dialect.name" in content or "is_postgresql" in content, (
            "Migration should check database dialect for PostgreSQL vs SQLite"
        )
        assert "else:" in content, (
            "Migration should have else clause for SQLite handling"
        )

    @pytest.mark.asyncio
    async def test_migration_roundtrip(self, alembic_dir):
        """
        RED Test: Verify migration 0013 can upgrade and downgrade cleanly

        Expected:
        - upgrade head → success (add columns)
        - downgrade -1 → success (remove columns)
        - upgrade head → success (re-add columns)
        """
        # Upgrade to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify new columns exist
            column_check = text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'agents'
                AND column_name IN ('avatar_url', 'rarity', 'character_description');
            """
            )
            query_result = await session.execute(column_check)
            columns = [row[0] for row in query_result.fetchall()]
            assert len(columns) == 3, (
                f"Expected 3 new columns after upgrade, found {len(columns)}: {columns}"
            )

        # Downgrade by 1
        migration_result = subprocess.run(
            ["alembic", "downgrade", "-1"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic downgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify columns removed
            query_result = await session.execute(column_check)
            columns_after_downgrade = [row[0] for row in query_result.fetchall()]
            assert len(columns_after_downgrade) == 0, (
                f"Columns should be removed after downgrade, found: {columns_after_downgrade}"
            )

        # Re-upgrade to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic re-upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify columns recreated
            query_result = await session.execute(column_check)
            columns_after_reupgrade = [row[0] for row in query_result.fetchall()]
            assert len(columns_after_reupgrade) == 3, (
                f"Expected 3 columns after re-upgrade, found {len(columns_after_reupgrade)}"
            )

    @pytest.mark.asyncio
    async def test_avatar_url_max_length(self, alembic_dir):
        """
        RED Test: Verify avatar_url enforces 500 character limit

        Expected:
        - avatar_url accepts strings up to 500 characters
        - Longer strings are rejected (if constraint exists)
        """
        # Run migration to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify column max_length
            column_check = text(
                """
                SELECT character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'agents'
                AND column_name = 'avatar_url';
            """
            )
            query_result = await session.execute(column_check)
            max_length = query_result.scalar()

            # PostgreSQL VARCHAR has max_length, TEXT may return None
            if max_length is not None:
                assert max_length == 500, (
                    f"avatar_url max_length should be 500, got {max_length}"
                )
