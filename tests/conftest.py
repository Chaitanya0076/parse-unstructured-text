import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
import sqlalchemy
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-v1-test-dummy")
os.environ.setdefault("API_KEY", "test-api-key")
os.environ.setdefault("EXTRACTION_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
os.environ.setdefault("CLASSIFICATION_MODEL", "qwen/qwen-2.5-72b-instruct:free")
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://parseuser:parsepass@localhost:5432/parse_unstructured_text_test",
    ),
)

from app.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db import models  # noqa: F401,E402
from app.deps import get_db_session, get_extraction_service  # noqa: E402
from app.main import app  # noqa: E402
from app.services.extraction import ExtractionService  # noqa: E402

settings = get_settings()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = session_factory(bind=connection)

    nested = await connection.begin_nested()

    @sqlalchemy.event.listens_for(session.sync_session, "after_transaction_end")
    def restart_savepoint(sync_session, sync_transaction):
        nonlocal nested
        if nested.is_active:
            return
        nested = connection.sync_connection.begin_nested()

    try:
        yield session
    finally:
        await session.close()
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()


@pytest.fixture
def mock_llm_client():
    return AsyncMock()


@pytest_asyncio.fixture
async def client(db_session, mock_llm_client):
    async def _override_get_db_session():
        yield db_session

    def _override_get_extraction_service():
        return ExtractionService(
            client=mock_llm_client,
            extraction_model=settings.extraction_model,
            classification_model=settings.classification_model,
        )

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_extraction_service] = _override_get_extraction_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def api_key_headers():
    return {"X-API-Key": settings.api_key}


def make_parsed_response(payload):
    """Build a fake OpenAI chat-completion response whose message content is the
    JSON-encoded payload (a BaseModel instance or a plain dict)."""
    if hasattr(payload, "model_dump_json"):
        content = payload.model_dump_json()
    else:
        content = json.dumps(payload, default=str)
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])
