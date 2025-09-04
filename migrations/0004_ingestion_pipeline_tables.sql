-- 0004: 문서 수집 파이프라인 테이블
-- 작성자: A팀 
-- 날짜: 2025-09-04

-- 수집 작업 테이블
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    doc_hash VARCHAR(64) NOT NULL,
    doc_type VARCHAR(20) NOT NULL CHECK (doc_type IN ('pdf', 'markdown', 'html')),
    content_type VARCHAR(100),
    size_bytes BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'dlq')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    chunks_created INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    content_blob BYTEA, -- 원본 콘텐츠 저장 (디버깅/재처리용)
    
    -- 인덱스
    INDEX idx_ingestion_jobs_status (status),
    INDEX idx_ingestion_jobs_doc_hash (doc_hash),
    INDEX idx_ingestion_jobs_created_at (created_at DESC),
    INDEX idx_ingestion_jobs_status_created (status, created_at DESC)
);

-- 수집 작업 통계 뷰
CREATE OR REPLACE VIEW ingestion_stats AS
SELECT 
    status,
    COUNT(*) as job_count,
    AVG(chunks_created) as avg_chunks_per_job,
    MAX(created_at) as last_job_time,
    SUM(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 ELSE 0 END) as jobs_last_24h
FROM ingestion_jobs
GROUP BY status;

-- documents 테이블 확장 (이미 존재하면 컬럼만 추가)
DO $$
BEGIN
    -- doc_hash 컬럼이 없으면 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'doc_hash') THEN
        ALTER TABLE documents ADD COLUMN doc_hash VARCHAR(64);
    END IF;
    
    -- doc_hash에 유니크 제약조건 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE table_name = 'documents' AND constraint_name = 'documents_doc_hash_unique') THEN
        ALTER TABLE documents ADD CONSTRAINT documents_doc_hash_unique UNIQUE (doc_hash);
    END IF;
    
    -- updated_at 컬럼이 없으면 추가
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'documents' AND column_name = 'updated_at') THEN
        ALTER TABLE documents ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- 수집 작업 자동 정리 함수 (30일 이상된 completed 작업 정리)
CREATE OR REPLACE FUNCTION cleanup_old_ingestion_jobs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM ingestion_jobs 
    WHERE status = 'completed' 
    AND created_at < NOW() - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- 감사 로그에 기록
    INSERT INTO audit_log (action, user_id, details)
    VALUES ('ingestion_cleanup', 'system', 
           json_build_object('deleted_jobs', deleted_count, 'cleanup_date', NOW()));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 수집 작업 정리 스케줄러 (매일 새벽 2시)
-- 실제 운영환경에서는 cron job이나 pg_cron 확장 사용 권장
-- 이 코멘트는 참고용: SELECT cron.schedule('cleanup-ingestion', '0 2 * * *', 'SELECT cleanup_old_ingestion_jobs();');

-- 수집 파이프라인 메트릭 함수
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

-- 샘플 메트릭 조회: SELECT get_ingestion_metrics('7 days');

COMMENT ON TABLE ingestion_jobs IS '문서 수집 파이프라인 작업 추적';
COMMENT ON FUNCTION cleanup_old_ingestion_jobs() IS '30일 이상된 완료 작업 자동 정리';
COMMENT ON FUNCTION get_ingestion_metrics(INTERVAL) IS '수집 파이프라인 성능 메트릭 조회';