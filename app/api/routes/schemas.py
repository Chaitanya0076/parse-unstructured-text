from fastapi import APIRouter, Depends

from app.deps import require_api_key
from app.registry import DOC_TYPE_REGISTRY
from app.schemas.api import SchemaInfo

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/v1/schemas", response_model=list[SchemaInfo])
async def list_schemas() -> list[SchemaInfo]:
    return [
        SchemaInfo(
            doc_type=doc_type,
            description=entry.description,
            json_schema=entry.model.model_json_schema(),
        )
        for doc_type, entry in DOC_TYPE_REGISTRY.items()
    ]
