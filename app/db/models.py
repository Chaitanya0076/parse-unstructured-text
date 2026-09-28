import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParsedDocument(Base):
    __tablename__ = "parsed_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    doc_type: Mapped[str] = mapped_column(index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    extracted_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_id: Mapped[str]
    status: Mapped[str] = mapped_column(index=True)
    error_detail: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
