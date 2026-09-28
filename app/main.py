from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from openai import AsyncOpenAI

from app.api.router import api_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.llm_client = AsyncOpenAI(
        api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url
    )
    try:
        yield
    finally:
        await app.state.llm_client.close()


app = FastAPI(title="Unstructured Text Parser", lifespan=lifespan)
app.include_router(api_router)
