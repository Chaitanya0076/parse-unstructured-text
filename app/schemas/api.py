import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ParseRequest(BaseModel):
    text: str
    doc_type: str | None = None


class DocumentOut(BaseModel):
    id: uuid.UUID
    doc_type: str
    status: str
    data: dict[str, Any] | None
    model_used: str
    created_at: datetime


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    total: int
    limit: int
    offset: int


class SchemaInfo(BaseModel):
    doc_type: str
    description: str
    json_schema: dict[str, Any]


class ExtractionFailedDetail(BaseModel):
    detail: str = "extraction_failed"
    doc_type: str
    errors: list[dict[str, Any]]
    attempt_count: int
