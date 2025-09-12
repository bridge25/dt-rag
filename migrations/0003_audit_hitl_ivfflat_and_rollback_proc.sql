-- Dynamic Taxonomy RAG v1.8.1 - Audit, HITL, Vector Indexes and Rollback
-- Migration: 0003_audit_hitl_ivfflat_and_rollback_proc.sql
-- Purpose: Audit logging, HITL queue, vector indexes, and taxonomy rollback procedures
-- Dependencies: 0001_initial_schema.sql, 0002_span_range_and_indexes.sql

-- 1. Audit Log Table (comprehensive system tracking)
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(100) NOT NULL, -- 'classify', 'search', 'taxonomy_update', 'rollback'
    actor TEXT NOT NULL DEFAULT current_user,
    target TEXT, -- entity being acted upon (doc_id, node_id, etc.)
    detail JSONB NOT NULL DEFAULT '{}', -- action-specific details
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT DEFAULT NULL, -- track user sessions
    ip_address INET DEFAULT NULL,
    
    -- Constraints
    CONSTRAINT valid_action_type CHECK (action IN (
        'classify', 'search', 'taxonomy_create', 'taxonomy_update', 'taxonomy_delete',
        'taxonomy_rollback', 'taxonomy_rollback_nodes', 'taxonomy_rollback_edges', 
        'taxonomy_rollback_completed', 'taxonomy_rollback_failed',
        'document_upload', 'document_process', 'embedding_create',
        'hitl_queue_add', 'hitl_resolve', 'user_login', 'system_error'
    )),
    CONSTRAINT valid_actor CHECK (length(actor) > 0)
);

-- 2. HITL Queue (Human-in-the-Loop for low confidence classifications)
CREATE TABLE hitl_queue (
    queue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL REFERENCES chunks(chunk_id) ON DELETE CASCADE,
    original_classification JSONB NOT NULL, -- ClassifyResponse with low confidence
    suggested_paths TEXT[] NOT NULL, -- AI suggested paths
    confidence REAL NOT NULL,
    priority INTEGER DEFAULT 3, -- 1=urgent, 2=high, 3=normal, 4=low, 5=backlog
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'assigned', 'resolved', 'skipped'
    assigned_to TEXT DEFAULT NULL,
    assigned_at TIMESTAMP DEFAULT NULL,
    resolved_at TIMESTAMP DEFAULT NULL,
    resolution JSONB DEFAULT NULL, -- final human decision
    notes TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_confidence_range CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 5),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'assigned', 'resolved', 'skipped')),
    CONSTRAINT assignment_logic CHECK (
        (status = 'assigned' AND assigned_to IS NOT NULL AND assigned_at IS NOT NULL) OR
        (status != 'assigned')
    ),
    CONSTRAINT resolution_logic CHECK (
        (status = 'resolved' AND resolved_at IS NOT NULL AND resolution IS NOT NULL) OR
        (status != 'resolved')
    )
);

-- 3. IVFFlat vector index for efficient similarity search
-- Check if ivfflat is available before creating index
DO $$
BEGIN
    -- Only create ivfflat index if the extension is available
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        -- Check if ivfflat access method is available (pgvector 0.5.0+)
        IF EXISTS (SELECT 1 FROM pg_am WHERE amname = 'ivfflat') THEN
            EXECUTE 'CREATE INDEX IF NOT EXISTS idx_embeddings_vec_ivf ON embeddings USING ivfflat (vec vector_cosine_ops) WITH (lists = 100)';
            RAISE NOTICE 'Created IVFFlat index for vector similarity search';
        ELSE
            -- Fallback to regular vector index if ivfflat not available
            EXECUTE 'CREATE INDEX IF NOT EXISTS idx_embeddings_vec ON embeddings USING btree (vec)';
            RAISE NOTICE 'Created regular index on embeddings (IVFFlat not available)';
        END IF;
    ELSE
        RAISE NOTICE 'pgvector extension not found - skipping vector indexes';
    END IF;
END $$;

-- 4. Additional performance indexes
CREATE INDEX idx_audit_log_timestamp ON audit_log (timestamp DESC);
CREATE INDEX idx_audit_log_action_actor ON audit_log (action, actor);
CREATE INDEX idx_audit_log_target ON audit_log (target) WHERE target IS NOT NULL;

CREATE INDEX idx_hitl_queue_status_priority ON hitl_queue (status, priority, created_at);
CREATE INDEX idx_hitl_queue_confidence ON hitl_queue (confidence) WHERE confidence < 0.7;
CREATE INDEX idx_hitl_queue_assigned ON hitl_queue (assigned_to, assigned_at) WHERE assigned_to IS NOT NULL;

-- 5. Taxonomy Rollback Procedure
CREATE OR REPLACE PROCEDURE taxonomy_rollback(to_v INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    current_v INTEGER;
    rollback_count INTEGER;
    chunk_record RECORD;
BEGIN
    -- Validate target version exists
    SELECT MAX(version) INTO current_v FROM taxonomy_nodes;
    
    IF to_v >= current_v THEN
        RAISE EXCEPTION 'Cannot rollback to version % (current: %)', to_v, current_v;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM taxonomy_nodes WHERE version = to_v) THEN
        RAISE EXCEPTION 'Target version % does not exist', to_v;
    END IF;
    
    -- Log rollback initiation
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback', current_user, to_v::text, 
           jsonb_build_object('from_version', current_v, 'to_version', to_v, 'status', 'started'));
    
    -- Rollback doc_taxonomy mappings to target version
    FOR chunk_record IN 
        SELECT DISTINCT dt.doc_id, dt.path 
        FROM doc_taxonomy dt
        JOIN taxonomy_nodes tn ON dt.path = tn.canonical_path
        WHERE tn.version > to_v
    LOOP
        -- Find equivalent path in target version or remove mapping
        IF EXISTS (
            SELECT 1 FROM taxonomy_nodes 
            WHERE canonical_path = chunk_record.path AND version = to_v
        ) THEN
            -- Path exists in target version, keep mapping
            CONTINUE;
        ELSE
            -- Path doesn't exist, remove mapping
            DELETE FROM doc_taxonomy 
            WHERE doc_id = chunk_record.doc_id AND path = chunk_record.path;
            
            -- Log removal
            INSERT INTO audit_log (action, actor, target, detail) 
            VALUES ('taxonomy_rollback', current_user, chunk_record.doc_id::text,
                   jsonb_build_object('removed_path', chunk_record.path, 'reason', 'path_not_in_target_version'));
        END IF;
    END LOOP;
    
    -- Remove edges from versions newer than target
    DELETE FROM taxonomy_edges WHERE version > to_v;
    GET DIAGNOSTICS rollback_count = ROW_COUNT;
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback_edges', current_user, to_v::text, 
           jsonb_build_object('deleted_edges', rollback_count));
    
    -- Remove nodes from versions newer than target
    DELETE FROM taxonomy_nodes WHERE version > to_v;
    GET DIAGNOSTICS rollback_count = ROW_COUNT;
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback_nodes', current_user, to_v::text, 
           jsonb_build_object('deleted_nodes', rollback_count));
    
    -- Record migration
    INSERT INTO taxonomy_migrations (from_version, to_version, migration_type, changes)
    VALUES (current_v, to_v, 'rollback', jsonb_build_object(
        'rollback_timestamp', CURRENT_TIMESTAMP,
        'deleted_nodes', rollback_count,
        'performer', current_user
    ));
    
    -- Log successful completion
    INSERT INTO audit_log (action, actor, target, detail) 
    VALUES ('taxonomy_rollback_completed', current_user, to_v::text, 
           jsonb_build_object('rollback_target', to_v, 'status', 'success', 'duration_seconds', 
           EXTRACT(epoch FROM (CURRENT_TIMESTAMP - (SELECT timestamp FROM audit_log WHERE action = 'taxonomy_rollback' ORDER BY timestamp DESC LIMIT 1)))));
    
    -- Update statistics
    ANALYZE taxonomy_nodes;
    ANALYZE taxonomy_edges;
    ANALYZE doc_taxonomy;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log error details
        INSERT INTO audit_log (action, actor, target, detail) 
        VALUES ('taxonomy_rollback_failed', current_user, to_v::text, 
               jsonb_build_object('error', SQLERRM, 'sqlstate', SQLSTATE, 'hint', COALESCE(SQLERRM_DETAIL, 'None')));
        RAISE;
END $$;

-- 6. HITL Queue Management Functions
CREATE OR REPLACE FUNCTION add_to_hitl_queue(
    p_chunk_id UUID,
    p_classification JSONB,
    p_suggested_paths TEXT[],
    p_confidence REAL
) RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    queue_id UUID;
BEGIN
    INSERT INTO hitl_queue (chunk_id, original_classification, suggested_paths, confidence)
    VALUES (p_chunk_id, p_classification, p_suggested_paths, p_confidence)
    RETURNING hitl_queue.queue_id INTO queue_id;
    
    -- Log HITL queue addition
    INSERT INTO audit_log (action, actor, target, detail)
    VALUES ('hitl_queue_add', current_user, p_chunk_id::text,
           jsonb_build_object('queue_id', queue_id, 'confidence', p_confidence, 'suggested_paths', p_suggested_paths));
    
    RETURN queue_id;
END $$;

-- 7. Utility views for common queries
CREATE VIEW v_low_confidence_classifications AS
SELECT 
    hq.queue_id,
    hq.chunk_id,
    c.text,
    d.title as document_title,
    hq.suggested_paths,
    hq.confidence,
    hq.status,
    hq.created_at,
    hq.assigned_to
FROM hitl_queue hq
JOIN chunks c ON hq.chunk_id = c.chunk_id
JOIN documents d ON c.doc_id = d.doc_id
WHERE hq.status = 'pending'
ORDER BY hq.priority, hq.created_at;

CREATE VIEW v_taxonomy_version_summary AS
SELECT 
    version,
    COUNT(*) as node_count,
    MAX(created_at) as last_modified,
    COUNT(DISTINCT array_to_string(canonical_path[1:1], '')) as root_categories
FROM taxonomy_nodes
WHERE is_active = TRUE
GROUP BY version
ORDER BY version DESC;

-- 8. Triggers for automatic audit logging
CREATE OR REPLACE FUNCTION audit_taxonomy_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (action, target, detail)
        VALUES ('taxonomy_create', NEW.node_id::text, 
               jsonb_build_object('canonical_path', NEW.canonical_path, 'version', NEW.version));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (action, target, detail)
        VALUES ('taxonomy_update', NEW.node_id::text,
               jsonb_build_object('old_path', OLD.canonical_path, 'new_path', NEW.canonical_path, 'version', NEW.version));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (action, target, detail)
        VALUES ('taxonomy_delete', OLD.node_id::text,
               jsonb_build_object('canonical_path', OLD.canonical_path, 'version', OLD.version));
        RETURN OLD;
    END IF;
    RETURN NULL;
END $$;

-- Apply triggers
CREATE TRIGGER tr_audit_taxonomy_nodes
    AFTER INSERT OR UPDATE OR DELETE ON taxonomy_nodes
    FOR EACH ROW EXECUTE FUNCTION audit_taxonomy_changes();

-- Comments for documentation
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all system actions';
COMMENT ON TABLE hitl_queue IS 'Human-in-the-Loop queue for low confidence classifications';
COMMENT ON PROCEDURE taxonomy_rollback IS 'Safe rollback procedure with full audit trail';

-- Conditional comment for index (only if it exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_embeddings_vec_ivf') THEN
        COMMENT ON INDEX idx_embeddings_vec_ivf IS 'IVFFlat index for fast vector similarity search (lists=100)';
    END IF;
END $$;

COMMENT ON VIEW v_low_confidence_classifications IS 'Pending HITL items with document context';
COMMENT ON VIEW v_taxonomy_version_summary IS 'Version-wise taxonomy statistics';

-- Final statistics update (conditional for safety)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log') THEN
        ANALYZE audit_log;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'hitl_queue') THEN
        ANALYZE hitl_queue;
    END IF;
END $$;