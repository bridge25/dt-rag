# @TEST:SCHEMA-SYNC-001:MODEL
"""
DocTaxonomy 모델 스키마 정합성 테스트
"""
import pytest
from sqlalchemy import inspect
from apps.api.database import DocTaxonomy

def test_doc_taxonomy_composite_pk():
    """Composite Primary Key (doc_id, node_id, version) 확인"""
    inspector = inspect(DocTaxonomy)
    pk_columns = [col.name for col in inspector.primary_key]

    assert len(pk_columns) == 3, f"Expected 3 PK columns, got {len(pk_columns)}"
    assert "doc_id" in pk_columns
    assert "node_id" in pk_columns
    assert "version" in pk_columns

def test_doc_taxonomy_mapping_id_removed():
    """mapping_id 필드가 제거되었는지 확인"""
    inspector = inspect(DocTaxonomy)
    columns = [col.name for col in inspector.columns]

    assert "mapping_id" not in columns, "mapping_id field should be removed"

def test_doc_taxonomy_not_null_fields():
    """NOT NULL 제약이 올바르게 설정되었는지 확인"""
    inspector = inspect(DocTaxonomy)

    required_fields = ["doc_id", "node_id", "version", "path", "confidence"]
    for field_name in required_fields:
        col = next((c for c in inspector.columns if c.name == field_name), None)
        assert col is not None, f"Field {field_name} not found"
        assert not col.nullable, f"Field {field_name} should be NOT NULL"

def test_doc_taxonomy_created_at_auto():
    """created_at 필드에 server_default가 설정되었는지 확인"""
    inspector = inspect(DocTaxonomy)
    created_at_col = next((c for c in inspector.columns if c.name == "created_at"), None)

    assert created_at_col is not None, "created_at field not found"
    assert created_at_col.server_default is not None, "created_at should have server_default"
