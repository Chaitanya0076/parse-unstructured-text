from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.base import get_session
from app.services.extraction import ExtractionService

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


def require_api_key(
    provided_key: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    if provided_key is None or provided_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


def get_extraction_service(request: Request, settings: Settings = Depends(get_settings)) -> ExtractionService:
    return ExtractionService(
        client=request.app.state.llm_client,
        extraction_model=settings.extraction_model,
        classification_model=settings.classification_model,
    )
