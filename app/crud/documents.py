import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ParsedDocument


async def create_document(
    session: AsyncSession,
    *,
    doc_type: str,
    raw_text: str,
    model_id: str,
    status: str,
    extracted_json: dict[str, Any] | None = None,
    error_detail: Any | None = None,
) -> ParsedDocument:
    document = ParsedDocument(
        doc_type=doc_type,
        raw_text=raw_text,
        model_id=model_id,
        status=status,
        extracted_json=extracted_json,
        error_detail=error_detail,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def get_document(session: AsyncSession, document_id: uuid.UUID) -> ParsedDocument | None:
    return await session.get(ParsedDocument, document_id)


async def list_documents(
    session: AsyncSession,
    *,
    doc_type: str | None,
    status: str | None,
    limit: int,
    offset: int,
) -> tuple[list[ParsedDocument], int]:
    filters = []
    if doc_type is not None:
        filters.append(ParsedDocument.doc_type == doc_type)
    if status is not None:
        filters.append(ParsedDocument.status == status)

    count_stmt = select(func.count()).select_from(ParsedDocument).filter(*filters)
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = (
        select(ParsedDocument)
        .filter(*filters)
        .order_by(ParsedDocument.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list((await session.execute(stmt)).scalars().all())
    return items, total
