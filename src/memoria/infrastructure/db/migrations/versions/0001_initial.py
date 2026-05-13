"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "memory_chains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", JSON(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "memory_issues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("status_confidence", sa.Float(), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=False),
        sa.Column("tags", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "patch_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("patch_json", JSON(), nullable=False),
        sa.Column("before_json", JSON(), nullable=False),
        sa.Column("after_json", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "proposals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_type", sa.String(length=80), nullable=False),
        sa.Column("payload", JSON(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "raw_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("tags", JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=True),
        sa.Column("meta", JSON(), nullable=False),
        sa.Column("processing_state", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_entry_id", sa.Integer(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=300), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("mtime", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["raw_entry_id"], ["raw_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chain_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("target_type", sa.String(length=40), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("user_locked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chain_id"], ["memory_chains.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "import_audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_entry_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("meta", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["raw_entry_id"], ["raw_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "issue_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_issue_id", sa.Integer(), nullable=False),
        sa.Column("target_issue_id", sa.Integer(), nullable=False),
        sa.Column("link_type", sa.String(length=60), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["source_issue_id"], ["memory_issues.id"]),
        sa.ForeignKeyConstraint(["target_issue_id"], ["memory_issues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "llm_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("reasoning_effort", sa.String(length=40), nullable=False),
        sa.Column("strictness", sa.String(length=40), nullable=False),
        sa.Column("transcript_path", sa.Text(), nullable=True),
        sa.Column("transcript_sha256", sa.String(length=64), nullable=True),
        sa.Column("final_report_json", JSON(), nullable=False),
        sa.Column("patch_id", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["patch_id"], ["patch_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "memory_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_entry_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("corrected_by_event_id", sa.Integer(), nullable=True),
        sa.Column("superseded_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["corrected_by_event_id"], ["memory_events.id"]),
        sa.ForeignKeyConstraint(["raw_entry_id"], ["raw_entries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "issue_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issue_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["memory_events.id"]),
        sa.ForeignKeyConstraint(["issue_id"], ["memory_issues.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sleep_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("report_json", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["llm_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("sleep_reports")
    op.drop_table("issue_comments")
    op.drop_table("memory_events")
    op.drop_table("llm_jobs")
    op.drop_table("issue_links")
    op.drop_table("import_audits")
    op.drop_table("chain_memberships")
    op.drop_table("attachments")
    op.drop_table("raw_entries")
    op.drop_table("proposals")
    op.drop_table("patch_records")
    op.drop_table("memory_issues")
    op.drop_table("memory_chains")
