-- =============================================================================
-- TrustMoss: PostgreSQL 16 Schema Initialization
-- Automated provisioning of tables, indexes, and pgcrypto extensions.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Trust Evaluation Audit Stream
CREATE TABLE IF NOT EXISTS trust_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(128) NOT NULL,
    query_id VARCHAR(128) NOT NULL,
    agent_id VARCHAR(64),
    query_text TEXT NOT NULL,
    answer_text TEXT,
    verdict VARCHAR(16) NOT NULL,
    trust_score NUMERIC(5, 4) NOT NULL,
    trust_color VARCHAR(16),
    relevance_result JSONB,
    groundedness_result JSONB,
    pii_result JSONB,
    evaluation_result JSONB,
    circuit_breaker_tripped BOOLEAN DEFAULT FALSE,
    context_chunks_count INTEGER,
    top_retrieval_score NUMERIC(5, 4),
    model_used VARCHAR(64),
    latency_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trust_events_session ON trust_events (session_id);
CREATE INDEX IF NOT EXISTS idx_trust_events_created ON trust_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trust_events_query ON trust_events (query_id);

-- 2. GDPR Art. 17 Immutable Compliance Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(64) NOT NULL,
    subject_id VARCHAR(128) NOT NULL,
    actor_id VARCHAR(64) DEFAULT 'system',
    details JSONB,
    gdpr_article VARCHAR(32),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_subject ON audit_log (subject_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log (created_at DESC);

-- 3. Human-in-the-Loop (HITL) Review Queue & Decisions
CREATE TABLE IF NOT EXISTS hitl_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id VARCHAR(128) UNIQUE NOT NULL,
    query_id VARCHAR(128) NOT NULL,
    session_id VARCHAR(128),
    query_text TEXT NOT NULL,
    answer_text TEXT,
    violation_type VARCHAR(64) NOT NULL,
    reason TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    operator_id VARCHAR(64),
    operator_notes TEXT,
    corrected_answer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hitl_records_status ON hitl_records (status);
CREATE INDEX IF NOT EXISTS idx_hitl_records_created ON hitl_records (created_at DESC);

-- 4. k6 OSS Scalability & Concurrency Benchmark Runs
CREATE TABLE IF NOT EXISTS load_test_runs (
    id VARCHAR(128) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    test_type VARCHAR(32) NOT NULL,
    target VARCHAR(512) NOT NULL,
    vus INTEGER NOT NULL,
    duration VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'CREATED',
    p95_ms NUMERIC(8, 2),
    p99_ms NUMERIC(8, 2),
    rps NUMERIC(10, 2),
    error_rate NUMERIC(6, 4),
    threshold_passed BOOLEAN,
    breaking_point VARCHAR(256),
    raw_metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_load_test_runs_created ON load_test_runs (created_at DESC);
