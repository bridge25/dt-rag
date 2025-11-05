"""
@TEST:AGENT-GROWTH-004:MIGRATION | Phase 3-1 Database Schema & Migration Tests

RED Phase: Migration tests for background_tasks and coverage_history tables.
Tests Alembic migration 0012_add_background_tasks_coverage_history.py
"""

import pytest
import subprocess
import os
from sqlalchemy import text
from apps.core.db_session import async_session


class TestAgentBackgroundTasksMigration:
    """Test suite for SPEC-AGENT-GROWTH-004 Phase 3-1 Database Migration"""

    @pytest.fixture(scope="class")
    def alembic_dir(self):
        """Return Alembic directory path"""
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    @pytest.mark.asyncio
    async def test_migration_0012_creates_background_tasks_table(self, alembic_dir):
        """
        RED Test: Verify migration 0012 creates background_tasks table with 15 columns

        Expected:
        - Table exists: background_tasks
        - Columns (15): task_id, agent_id, task_type, status, created_at, started_at,
          completed_at, result, error, webhook_url, webhook_retry_count,
          cancellation_requested, queue_position, progress_percentage, estimated_completion_at
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
            # Verify table exists
            table_check = text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'background_tasks'
                );
            """
            )
            query_result = await session.execute(table_check)
            table_exists = query_result.scalar()
            assert table_exists, "background_tasks table does not exist after migration"

            # Verify columns
            column_check = text(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'background_tasks'
                ORDER BY ordinal_position;
            """
            )
            query_result = await session.execute(column_check)
            columns = query_result.fetchall()

            column_names = [col[0] for col in columns]
            expected_columns = [
                "task_id",
                "agent_id",
                "task_type",
                "status",
                "created_at",
                "started_at",
                "completed_at",
                "result",
                "error",
                "webhook_url",
                "webhook_retry_count",
                "cancellation_requested",
                "queue_position",
                "progress_percentage",
                "estimated_completion_at",
            ]

            for expected_col in expected_columns:
                assert expected_col in column_names, (
                    f"Column '{expected_col}' missing in background_tasks table. "
                    f"Found columns: {column_names}"
                )

            # Verify NOT NULL constraints
            column_dict = {col[0]: col for col in columns}
            assert column_dict["task_id"][2] == "NO", "task_id should be NOT NULL"
            assert column_dict["agent_id"][2] == "NO", "agent_id should be NOT NULL"
            assert column_dict["task_type"][2] == "NO", "task_type should be NOT NULL"
            assert column_dict["status"][2] == "NO", "status should be NOT NULL"
            assert column_dict["created_at"][2] == "NO", "created_at should be NOT NULL"

            # Verify default values exist
            assert (
                column_dict["webhook_retry_count"][3] is not None
            ), "webhook_retry_count should have DEFAULT 0"
            assert (
                column_dict["cancellation_requested"][3] is not None
            ), "cancellation_requested should have DEFAULT FALSE"
            assert (
                column_dict["progress_percentage"][3] is not None
            ), "progress_percentage should have DEFAULT 0.0"

    @pytest.mark.asyncio
    async def test_migration_0012_creates_coverage_history_table(self, alembic_dir):
        """
        RED Test: Verify migration 0012 creates coverage_history table with 7 columns

        Expected:
        - Table exists: coverage_history
        - Columns (7): history_id, agent_id, timestamp, overall_coverage,
          total_documents, total_chunks, version
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
            # Verify table exists
            table_check = text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'coverage_history'
                );
            """
            )
            query_result = await session.execute(table_check)
            table_exists = query_result.scalar()
            assert table_exists, "coverage_history table does not exist after migration"

            # Verify columns
            column_check = text(
                """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'coverage_history'
                ORDER BY ordinal_position;
            """
            )
            query_result = await session.execute(column_check)
            columns = query_result.fetchall()

            column_names = [col[0] for col in columns]
            expected_columns = [
                "history_id",
                "agent_id",
                "timestamp",
                "overall_coverage",
                "total_documents",
                "total_chunks",
                "version",
            ]

            for expected_col in expected_columns:
                assert expected_col in column_names, (
                    f"Column '{expected_col}' missing in coverage_history table. "
                    f"Found columns: {column_names}"
                )

            # Verify NOT NULL constraints
            column_dict = {col[0]: col for col in columns}
            assert column_dict["history_id"][2] == "NO", "history_id should be NOT NULL"
            assert column_dict["agent_id"][2] == "NO", "agent_id should be NOT NULL"
            assert column_dict["timestamp"][2] == "NO", "timestamp should be NOT NULL"
            assert (
                column_dict["overall_coverage"][2] == "NO"
            ), "overall_coverage should be NOT NULL"
            assert (
                column_dict["total_documents"][2] == "NO"
            ), "total_documents should be NOT NULL"
            assert (
                column_dict["total_chunks"][2] == "NO"
            ), "total_chunks should be NOT NULL"
            assert column_dict["version"][2] == "NO", "version should be NOT NULL"

            # Verify default values
            assert "gen_random_uuid()" in str(
                column_dict["history_id"][3]
            ), "history_id should have gen_random_uuid() default"
            assert "1.0.0" in str(
                column_dict["version"][3]
            ), "version should have DEFAULT '1.0.0'"

    @pytest.mark.asyncio
    async def test_background_tasks_indexes(self, alembic_dir):
        """
        RED Test: Verify background_tasks table has 4 required indexes

        Expected indexes:
        - idx_background_tasks_agent_id
        - idx_background_tasks_status
        - idx_background_tasks_created_at
        - idx_background_tasks_agent_status
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
            # Query indexes
            index_check = text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'background_tasks'
                ORDER BY indexname;
            """
            )
            query_result = await session.execute(index_check)
            indexes = query_result.fetchall()

            index_names = [idx[0] for idx in indexes]
            required_indexes = [
                "idx_background_tasks_agent_id",
                "idx_background_tasks_status",
                "idx_background_tasks_created_at",
                "idx_background_tasks_agent_status",
            ]

            for required_idx in required_indexes:
                assert required_idx in index_names, (
                    f"Index '{required_idx}' missing on background_tasks table. "
                    f"Found indexes: {index_names}"
                )

            # Verify idx_background_tasks_created_at is DESC
            idx_created_at = next(
                (idx for idx in indexes if idx[0] == "idx_background_tasks_created_at"),
                None,
            )
            if idx_created_at:
                assert (
                    "DESC" in idx_created_at[1]
                ), "idx_background_tasks_created_at should be DESC ordered"

    @pytest.mark.asyncio
    async def test_coverage_history_indexes(self, alembic_dir):
        """
        RED Test: Verify coverage_history table has 3 required indexes

        Expected indexes:
        - idx_coverage_history_agent_id
        - idx_coverage_history_timestamp
        - idx_coverage_history_agent_timestamp
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
            # Query indexes
            index_check = text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'coverage_history'
                ORDER BY indexname;
            """
            )
            query_result = await session.execute(index_check)
            indexes = query_result.fetchall()

            index_names = [idx[0] for idx in indexes]
            required_indexes = [
                "idx_coverage_history_agent_id",
                "idx_coverage_history_timestamp",
                "idx_coverage_history_agent_timestamp",
            ]

            for required_idx in required_indexes:
                assert required_idx in index_names, (
                    f"Index '{required_idx}' missing on coverage_history table. "
                    f"Found indexes: {index_names}"
                )

            # Verify idx_coverage_history_timestamp is DESC
            idx_timestamp = next(
                (idx for idx in indexes if idx[0] == "idx_coverage_history_timestamp"),
                None,
            )
            if idx_timestamp:
                assert (
                    "DESC" in idx_timestamp[1]
                ), "idx_coverage_history_timestamp should be DESC ordered"

    @pytest.mark.asyncio
    async def test_background_tasks_foreign_keys(self, alembic_dir):
        """
        RED Test: Verify background_tasks.agent_id has FK to agents.agent_id with ON DELETE CASCADE

        Expected:
        - Foreign key exists: background_tasks.agent_id -> agents.agent_id
        - Delete rule: CASCADE
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
            # Query foreign keys
            fk_check = text(
                """
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    JOIN information_schema.referential_constraints AS rc
                      ON rc.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'background_tasks'
                AND kcu.column_name = 'agent_id';
            """
            )
            query_result = await session.execute(fk_check)
            fk = query_result.fetchone()

            assert (
                fk is not None
            ), "Foreign key on background_tasks.agent_id does not exist"
            assert fk[3] == "agents", "Foreign key should reference 'agents' table"
            assert fk[4] == "agent_id", "Foreign key should reference 'agent_id' column"
            assert fk[5] == "CASCADE", "Foreign key should have ON DELETE CASCADE"

    @pytest.mark.asyncio
    async def test_coverage_history_constraints(self, alembic_dir):
        """
        RED Test: Verify coverage_history table has CHECK constraints

        Expected constraints:
        - overall_coverage >= 0.0 AND overall_coverage <= 100.0
        - total_documents >= 0
        - total_chunks >= 0
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
            # Query CHECK constraints
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
                AND tc.table_name = 'coverage_history';
            """
            )
            query_result = await session.execute(constraint_check)
            constraints = query_result.fetchall()

            constraint_clauses = [c[1] for c in constraints]

            # Verify coverage constraint
            coverage_constraint_exists = any(
                "overall_coverage" in clause and (">=" in clause or "<=") in clause
                for clause in constraint_clauses
            )
            assert coverage_constraint_exists, (
                "overall_coverage CHECK constraint not found. "
                f"Found constraints: {constraint_clauses}"
            )

            # Verify documents constraint
            documents_constraint_exists = any(
                "total_documents" in clause and ">=" in clause
                for clause in constraint_clauses
            )
            assert documents_constraint_exists, (
                "total_documents CHECK constraint (>= 0) not found. "
                f"Found constraints: {constraint_clauses}"
            )

            # Verify chunks constraint
            chunks_constraint_exists = any(
                "total_chunks" in clause and ">=" in clause
                for clause in constraint_clauses
            )
            assert chunks_constraint_exists, (
                "total_chunks CHECK constraint (>= 0) not found. "
                f"Found constraints: {constraint_clauses}"
            )

    @pytest.mark.asyncio
    async def test_migration_roundtrip(self, alembic_dir):
        """
        RED Test: Verify migration 0012 can upgrade and downgrade cleanly

        Expected:
        - upgrade head → success
        - downgrade -1 → success (remove both tables)
        - upgrade head → success (recreate both tables)
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
            # Verify tables exist
            table_check = text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('background_tasks', 'coverage_history');
            """
            )
            query_result = await session.execute(table_check)
            tables = [row[0] for row in query_result.fetchall()]
            assert (
                "background_tasks" in tables
            ), "background_tasks should exist after upgrade"
            assert (
                "coverage_history" in tables
            ), "coverage_history should exist after upgrade"

        # Downgrade by 1
        migration_result = subprocess.run(
            ["alembic", "downgrade", "-1"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic downgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify tables removed
            query_result = await session.execute(table_check)
            tables_after_downgrade = [row[0] for row in query_result.fetchall()]
            assert (
                "background_tasks" not in tables_after_downgrade
            ), "background_tasks should be removed after downgrade"
            assert (
                "coverage_history" not in tables_after_downgrade
            ), "coverage_history should be removed after downgrade"

        # Re-upgrade to head
        migration_result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )
        assert migration_result.returncode == 0, f"Alembic re-upgrade failed: {migration_result.stderr}"

        async with async_session() as session:
            # Verify tables recreated
            query_result = await session.execute(table_check)
            tables_after_reupgrade = [row[0] for row in query_result.fetchall()]
            assert (
                "background_tasks" in tables_after_reupgrade
            ), "background_tasks should be recreated after re-upgrade"
            assert (
                "coverage_history" in tables_after_reupgrade
            ), "coverage_history should be recreated after re-upgrade"
