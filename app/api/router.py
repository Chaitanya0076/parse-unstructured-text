from fastapi import APIRouter

from app.api.routes import documents, health, parse, schemas

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(schemas.router)
api_router.include_router(parse.router)
api_router.include_router(documents.router)
