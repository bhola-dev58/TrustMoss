"""
Initial schema migration — TrustMoss core tables

Revision ID: 0001
Create Date: 2026-09-17

Tables created:
  - trust_events  — Every intercepted agent interaction with trust verdict
  - hitl_reviews  — Human-in-the-loop review queue and decisions
  - audit_log     — Immutable GDPR/compliance audit trail
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── trust_events ─────────────────────────────────────────────────────────
    # Stores every intercepted agent query/response pair with its trust verdict.
    # This is the core telemetry table for the TrustMoss reliability gateway.
    op.create_table(
        "trust_events",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("session_id", sa.String(128), nullable=False, index=True),
        sa.Column("query_id", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column("agent_id", sa.String(128), nullable=True, index=True),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("answer_text", sa.Text, nullable=True),

        # Trust scoring outputs
        sa.Column("verdict", sa.String(16), nullable=False),    # PASS | WARN | FAIL
        sa.Column("trust_score", sa.Float, nullable=False),     # 0.0 – 1.0
        sa.Column("trust_color", sa.String(16), nullable=True), # green | yellow | red

        # Guardrail results (stored as JSONB for queryability)
        sa.Column("relevance_result", JSONB, nullable=True),
        sa.Column("groundedness_result", JSONB, nullable=True),
        sa.Column("pii_result", JSONB, nullable=True),
        sa.Column("evaluation_result", JSONB, nullable=True),

        # Circuit breaker state
        sa.Column("circuit_breaker_tripped", sa.Boolean, default=False, nullable=False),

        # RAG context metadata
        sa.Column("context_chunks_count", sa.Integer, nullable=True),
        sa.Column("top_retrieval_score", sa.Float, nullable=True),
        sa.Column("model_used", sa.String(128), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),

        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── hitl_reviews ──────────────────────────────────────────────────────────
    # Human-in-the-loop review queue: escalated trust events awaiting reviewer decision.
    op.create_table(
        "hitl_reviews",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column(
            "trust_event_id", UUID(as_uuid=True),
            sa.ForeignKey("trust_events.id", ondelete="CASCADE"),
            nullable=False, index=True
        ),
        sa.Column("query_id", sa.String(128), nullable=False, index=True),

        # Queue state machine
        sa.Column("status", sa.String(32), nullable=False, default="pending",
                  index=True),  # pending | in_review | approved | rejected | escalated

        # Priority (derived from HITL_VERDICT_V1 CRISPE template)
        sa.Column("hitl_priority", sa.String(16), nullable=True),   # LOW | MEDIUM | HIGH | URGENT
        sa.Column("recommended_action", sa.String(64), nullable=True),

        # Reviewer assignment
        sa.Column("assigned_to", sa.String(128), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),

        # Decision fields (filled when reviewed)
        sa.Column("reviewer_id", sa.String(128), nullable=True),
        sa.Column("decision", sa.String(32), nullable=True),        # approve | reject | modify
        sa.Column("trust_delta", sa.Float, nullable=True),          # +/- trust score adjustment
        sa.Column("reviewer_notes", sa.Text, nullable=True),
        sa.Column("changes_made", JSONB, nullable=True),

        # GDPR compliance log (per HITL_VERDICT_V1 template output)
        sa.Column("compliance_log", JSONB, nullable=True),

        # Escalation history
        sa.Column("escalation_count", sa.Integer, default=0, nullable=False),
        sa.Column("last_escalated_at", sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),

        # GDPR: TTL marker for automated purge (90-day default per retention.py)
        sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True),
    )

    # ── audit_log ─────────────────────────────────────────────────────────────
    # Immutable append-only audit trail. No updates or deletes in application code.
    # All GDPR Article 30 processing record obligations are logged here.
    op.create_table(
        "audit_log",
        sa.Column(
            "id", UUID(as_uuid=True), primary_key=True,
            server_default=sa.text("gen_random_uuid()"), nullable=False
        ),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        # e.g. TRUST_VERDICT | HITL_ESCALATED | PII_DETECTED | SECRET_ROTATION
        # | GDPR_ERASURE | DATA_EXPORT | CIRCUIT_BREAKER_TRIP

        sa.Column("actor_id", sa.String(128), nullable=True, index=True),
        sa.Column("subject_id", sa.String(128), nullable=True, index=True),
        sa.Column("resource_type", sa.String(64), nullable=True),    # trust_event | hitl_review | session
        sa.Column("resource_id", sa.String(128), nullable=True, index=True),

        # Payload (JSONB — queryable, but never logged raw PII values)
        sa.Column("payload", JSONB, nullable=True),

        # GDPR Article reference for compliance logging
        sa.Column("gdpr_article", sa.String(32), nullable=True),     # e.g. Art.17, Art.30

        # Source metadata
        sa.Column("service", sa.String(64), nullable=True),          # gateway | guardrails | evaluation
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("trace_id", sa.String(128), nullable=True, index=True),

        # Immutable timestamp — no updated_at column intentional
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"), index=True
        ),

        # GDPR: TTL marker for automated purge (30-day default for audit logs)
        sa.Column("purge_after", sa.DateTime(timezone=True), nullable=True),
    )

    # ── Performance indexes ───────────────────────────────────────────────────
    op.create_index("ix_trust_events_verdict", "trust_events", ["verdict"])
    op.create_index("ix_trust_events_created_at", "trust_events", ["created_at"])
    op.create_index("ix_trust_events_circuit_breaker", "trust_events", ["circuit_breaker_tripped"])
    op.create_index("ix_hitl_reviews_status_priority", "hitl_reviews", ["status", "hitl_priority"])
    op.create_index("ix_audit_log_event_type_created", "audit_log", ["event_type", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_event_type_created", table_name="audit_log")
    op.drop_index("ix_hitl_reviews_status_priority", table_name="hitl_reviews")
    op.drop_index("ix_trust_events_circuit_breaker", table_name="trust_events")
    op.drop_index("ix_trust_events_created_at", table_name="trust_events")
    op.drop_index("ix_trust_events_verdict", table_name="trust_events")
    op.drop_table("audit_log")
    op.drop_table("hitl_reviews")
    op.drop_table("trust_events")
