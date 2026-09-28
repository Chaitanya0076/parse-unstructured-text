from typing import Literal

from openai import AsyncOpenAI
from pydantic import create_model

from app.registry import DOC_TYPE_REGISTRY
from app.services.llm_client import call_llm
from app.services.llm_json import strip_code_fences

CLASSIFICATION_SYSTEM_PROMPT = (
    "You classify unstructured business text into exactly one document type based on "
    "its content. Choose the single best-fitting type, even if the text is ambiguous. "
    "Respond with ONLY a JSON object matching the schema below — no prose, no markdown "
    "code fences, no explanation."
)


def _build_classification_model():
    doc_type_literal = Literal[tuple(DOC_TYPE_REGISTRY.keys())]
    return create_model("DocTypeClassification", doc_type=(doc_type_literal, ...))


async def classify_doc_type(client: AsyncOpenAI, model: str, text: str) -> str:
    classification_model = _build_classification_model()
    type_descriptions = "\n".join(
        f"- {key}: {entry.description}" for key, entry in DOC_TYPE_REGISTRY.items()
    )
    schema = classification_model.model_json_schema()
    system_prompt = (
        f"{CLASSIFICATION_SYSTEM_PROMPT}\n\nAvailable document types:\n{type_descriptions}"
        f"\n\nJSON schema:\n{schema}"
    )
    content = await call_llm(client, model, system_prompt, [{"role": "user", "content": text}])
    parsed = classification_model.model_validate_json(strip_code_fences(content))
    return parsed.doc_type
