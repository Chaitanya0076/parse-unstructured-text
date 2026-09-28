"""create parsed_documents table

Revision ID: 0001
Revises:
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "parsed_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("doc_type", sa.String(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("extracted_json", postgresql.JSONB(), nullable=True),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_detail", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_parsed_documents_doc_type", "parsed_documents", ["doc_type"])
    op.create_index("ix_parsed_documents_status", "parsed_documents", ["status"])
    op.create_index("ix_parsed_documents_created_at", "parsed_documents", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_parsed_documents_created_at", table_name="parsed_documents")
    op.drop_index("ix_parsed_documents_status", table_name="parsed_documents")
    op.drop_index("ix_parsed_documents_doc_type", table_name="parsed_documents")
    op.drop_table("parsed_documents")
