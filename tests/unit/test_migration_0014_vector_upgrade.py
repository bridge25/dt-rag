"""
@TEST:TAG-CASEBANK-MIGRATION-004
Test migration 0014 - Vector type upgrade

Verifies that migration 0014 properly upgrades case_bank.query_vector
from FLOAT[] to vector(1536) with HNSW index.
"""
# @TEST:TAG-CASEBANK-MIGRATION-004

import pytest
import importlib.util
import sys


class TestMigration0014Syntax:
    """Test migration file syntax and structure"""

    def test_migration_file_exists(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-1
        Verify migration file 0014 exists
        """
        import os
        migration_path = "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        assert os.path.exists(migration_path), f"Migration file not found: {migration_path}"

    def test_migration_has_required_functions(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-2
        Verify migration has upgrade() and downgrade() functions
        """
        # Load migration module
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        assert hasattr(migration, 'upgrade'), "Migration must have upgrade() function"
        assert hasattr(migration, 'downgrade'), "Migration must have downgrade() function"
        assert callable(migration.upgrade), "upgrade must be callable"
        assert callable(migration.downgrade), "downgrade must be callable"

    def test_migration_has_correct_revision_id(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-3
        Verify migration has correct revision metadata
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        assert hasattr(migration, 'revision'), "Migration must have revision"
        assert migration.revision == '0014', f"Expected revision '0014', got '{migration.revision}'"

        assert hasattr(migration, 'down_revision'), "Migration must have down_revision"
        assert migration.down_revision == '0013', f"Expected down_revision '0013', got '{migration.down_revision}'"

    def test_migration_docstring_documents_purpose(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-4
        Verify migration has documentation
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        assert migration.__doc__ is not None, "Migration must have docstring"
        assert 'vector' in migration.__doc__.lower(), "Docstring should mention vector"
        assert 'TAG-CASEBANK-MIGRATION-004' in migration.__doc__, "Docstring should reference TAG"


class TestMigration0014Logic:
    """Test migration logic and SQL operations"""

    def test_migration_checks_postgresql(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-5
        Verify migration skips non-PostgreSQL databases
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        # Verify upgrade function has PostgreSQL check
        import inspect
        upgrade_source = inspect.getsource(migration.upgrade)
        assert 'postgresql' in upgrade_source.lower(), "Migration should check for PostgreSQL"
        assert 'sqlite' in upgrade_source.lower(), "Migration should handle SQLite gracefully"

    def test_migration_creates_hnsw_index(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-6
        Verify migration creates HNSW index (user-approved Option A)
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        import inspect
        upgrade_source = inspect.getsource(migration.upgrade)
        assert 'hnsw' in upgrade_source.lower(), "Migration should create HNSW index"
        assert 'idx_case_bank_query_vector_hnsw' in upgrade_source, "Should use correct index name"

    def test_migration_uses_vector_1536(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-7
        Verify migration upgrades to vector(1536) type
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        import inspect
        upgrade_source = inspect.getsource(migration.upgrade)
        assert 'vector(1536)' in upgrade_source, "Migration should upgrade to vector(1536)"

    def test_migration_handles_existing_index(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-8
        Verify migration handles already-existing HNSW index gracefully
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        import inspect
        upgrade_source = inspect.getsource(migration.upgrade)
        assert 'IF NOT EXISTS' in upgrade_source, "Migration should check if index exists"

    def test_downgrade_removes_index(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-9
        Verify downgrade removes HNSW index
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        import inspect
        downgrade_source = inspect.getsource(migration.downgrade)
        assert 'DROP INDEX' in downgrade_source, "Downgrade should drop HNSW index"
        assert 'idx_case_bank_query_vector_hnsw' in downgrade_source, "Should drop correct index"

    def test_downgrade_restores_float_array(self):
        """
        @TEST:TAG-CASEBANK-MIGRATION-004-10
        Verify downgrade restores FLOAT[] type
        """
        spec = importlib.util.spec_from_file_location(
            "migration_0014",
            "/home/a/projects/dt-rag-standalone/alembic/versions/0014_upgrade_case_bank_vector_type.py"
        )
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)

        import inspect
        downgrade_source = inspect.getsource(migration.downgrade)
        assert 'FLOAT[]' in downgrade_source, "Downgrade should restore FLOAT[] type"
