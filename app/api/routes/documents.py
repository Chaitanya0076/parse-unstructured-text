import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.documents import get_document, list_documents
from app.deps import get_db_session, require_api_key
from app.schemas.api import DocumentListOut, DocumentOut

router = APIRouter(dependencies=[Depends(require_api_key)])


def _to_document_out(document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        doc_type=document.doc_type,
        status=document.status,
        data=document.extracted_json,
        model_used=document.model_id,
        created_at=document.created_at,
    )


@router.get("/v1/documents/{document_id}", response_model=DocumentOut)
async def get_document_by_id(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> DocumentOut:
    document = await get_document(session, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return _to_document_out(document)


@router.get("/v1/documents", response_model=DocumentListOut)
async def list_documents_endpoint(
    doc_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> DocumentListOut:
    items, total = await list_documents(
        session, doc_type=doc_type, status=status_filter, limit=limit, offset=offset
    )
    return DocumentListOut(
        items=[_to_document_out(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
