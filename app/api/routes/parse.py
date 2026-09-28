from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.crud.documents import create_document
from app.deps import get_db_session, get_extraction_service, require_api_key
from app.exceptions import ExtractionFailedError, LLMServiceError, UnknownDocTypeError, serializable_errors
from app.schemas.api import DocumentOut, ParseRequest
from app.services.extraction import ExtractionService

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.post("/v1/parse", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def parse_text(
    body: ParseRequest,
    session: AsyncSession = Depends(get_db_session),
    extraction_service: ExtractionService = Depends(get_extraction_service),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    try:
        outcome = await extraction_service.extract(body.text, body.doc_type)
    except UnknownDocTypeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ExtractionFailedError as exc:
        await create_document(
            session,
            doc_type=exc.doc_type,
            raw_text=body.text,
            model_id=settings.extraction_model,
            status="failed",
            error_detail=serializable_errors(exc.errors),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "detail": "extraction_failed",
                "doc_type": exc.doc_type,
                "errors": serializable_errors(exc.errors),
                "attempt_count": exc.attempt_count,
            },
        ) from exc

    document = await create_document(
        session,
        doc_type=outcome.doc_type,
        raw_text=body.text,
        model_id=settings.extraction_model,
        status="completed",
        extracted_json=outcome.data.model_dump(mode="json"),
    )
    return DocumentOut(
        id=document.id,
        doc_type=document.doc_type,
        status=document.status,
        data=document.extracted_json,
        model_used=document.model_id,
        created_at=document.created_at,
    )
