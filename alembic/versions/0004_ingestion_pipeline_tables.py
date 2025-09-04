"""
문서 수집 파이프라인 테이블 추가

Revision ID: 0004
Revises: 0003  
Create Date: 2025-09-04 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    """수집 파이프라인 테이블 생성"""
    
    # 수집 작업 테이블 생성
    op.create_table(
        'ingestion_jobs',
        sa.Column('job_id', sa.String(36), primary_key=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('doc_hash', sa.String(64), nullable=False),
        sa.Column('doc_type', sa.String(20), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('chunks_created', sa.Integer, server_default='0'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('content_blob', sa.LargeBinary, nullable=True),
        
        sa.CheckConstraint("doc_type IN ('pdf', 'markdown', 'html')", name='check_doc_type'),
        sa.CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed', 'dlq')", name='check_status')
    )
    
    # 인덱스 생성
    op.create_index('idx_ingestion_jobs_status', 'ingestion_jobs', ['status'])
    op.create_index('idx_ingestion_jobs_doc_hash', 'ingestion_jobs', ['doc_hash'])
    op.create_index('idx_ingestion_jobs_created_at', 'ingestion_jobs', ['created_at'], 
                   postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_ingestion_jobs_status_created', 'ingestion_jobs', ['status', 'created_at'],
                   postgresql_ops={'created_at': 'DESC'})
    
    # documents 테이블에 컬럼 추가 (존재하지 않는 경우만)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'documents' AND column_name = 'doc_hash') THEN
                ALTER TABLE documents ADD COLUMN doc_hash VARCHAR(64);
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                           WHERE table_name = 'documents' AND constraint_name = 'documents_doc_hash_unique') THEN
                ALTER TABLE documents ADD CONSTRAINT documents_doc_hash_unique UNIQUE (doc_hash);
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                           WHERE table_name = 'documents' AND column_name = 'updated_at') THEN
                ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            END IF;
        END $$;
    """)
    
    # 수집 작업 통계 뷰 생성
    op.execute("""
        CREATE OR REPLACE VIEW ingestion_stats AS
        SELECT 
            status,
            COUNT(*) as job_count,
            AVG(chunks_created) as avg_chunks_per_job,
            MAX(created_at) as last_job_time,
            SUM(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) as jobs_last_24h
        FROM ingestion_jobs
        GROUP BY status;
    """)
    
    # 정리 함수 생성
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_old_ingestion_jobs()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM ingestion_jobs 
            WHERE status = 'completed' 
            AND created_at < NOW() - INTERVAL '30 days';
            
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            
            INSERT INTO audit_log (action, user_id, details)
            VALUES ('ingestion_cleanup', 'system', 
                   json_build_object('deleted_jobs', deleted_count, 'cleanup_date', NOW()));
            
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # 메트릭 함수 생성
    op.execute("""
        CREATE OR REPLACE FUNCTION get_ingestion_metrics(
            time_window INTERVAL DEFAULT '24 hours'
        )
        RETURNS JSON AS $$
        DECLARE
            result JSON;
        BEGIN
            SELECT json_build_object(
                'time_window', time_window,
                'total_jobs', COUNT(*),
                'successful_jobs', COUNT(CASE WHEN status = 'completed' THEN 1 END),
                'failed_jobs', COUNT(CASE WHEN status = 'failed' OR status = 'dlq' THEN 1 END),
                'success_rate', ROUND(
                    COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / 
                    NULLIF(COUNT(*), 0) * 100, 2
                ),
                'avg_chunks_per_doc', ROUND(AVG(
                    CASE WHEN status = 'completed' THEN chunks_created END
                ), 2),
                'total_documents_processed', SUM(
                    CASE WHEN status = 'completed' THEN 1 ELSE 0 END
                ),
                'total_chunks_created', SUM(
                    CASE WHEN status = 'completed' THEN chunks_created ELSE 0 END
                )
            ) INTO result
            FROM ingestion_jobs
            WHERE created_at > NOW() - time_window;
            
            RETURN result;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade():
    """수집 파이프라인 테이블 제거"""
    
    # 함수 제거
    op.execute("DROP FUNCTION IF EXISTS get_ingestion_metrics(INTERVAL);")
    op.execute("DROP FUNCTION IF EXISTS cleanup_old_ingestion_jobs();")
    
    # 뷰 제거
    op.execute("DROP VIEW IF EXISTS ingestion_stats;")
    
    # documents 테이블에서 추가된 컬럼 제거
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
                       WHERE table_name = 'documents' AND constraint_name = 'documents_doc_hash_unique') THEN
                ALTER TABLE documents DROP CONSTRAINT documents_doc_hash_unique;
            END IF;
            
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = 'documents' AND column_name = 'doc_hash') THEN
                ALTER TABLE documents DROP COLUMN doc_hash;
            END IF;
            
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                       WHERE table_name = 'documents' AND column_name = 'updated_at') THEN
                ALTER TABLE documents DROP COLUMN updated_at;
            END IF;
        END $$;
    """)
    
    # 인덱스 제거
    op.drop_index('idx_ingestion_jobs_status_created', 'ingestion_jobs')
    op.drop_index('idx_ingestion_jobs_created_at', 'ingestion_jobs')
    op.drop_index('idx_ingestion_jobs_doc_hash', 'ingestion_jobs')
    op.drop_index('idx_ingestion_jobs_status', 'ingestion_jobs')
    
    # 테이블 제거
    op.drop_table('ingestion_jobs')