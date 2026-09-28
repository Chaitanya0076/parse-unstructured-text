from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.exceptions import ExtractionFailedError, UnknownDocTypeError
from app.registry import DOC_TYPE_REGISTRY
from app.services.classification import classify_doc_type
from app.services.llm_client import call_llm
from app.services.llm_json import strip_code_fences

MAX_ATTEMPTS = 2


@dataclass
class ExtractionOutcome:
    doc_type: str
    data: BaseModel


def _format_validation_errors(exc: ValidationError) -> str:
    lines = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"]) or "<root>"
        lines.append(f"- {loc}: {error['msg']}")
    return "\n".join(lines)


def _build_extraction_system_prompt(base_prompt: str, output_format: type[BaseModel]) -> str:
    schema = output_format.model_json_schema()
    return (
        f"{base_prompt}\n\n"
        "Respond with ONLY a single JSON object matching this JSON schema — no prose, "
        "no markdown code fences, no explanation.\n\n"
        f"JSON schema:\n{schema}"
    )


class ExtractionService:
    def __init__(self, client: AsyncOpenAI, extraction_model: str, classification_model: str):
        self._client = client
        self._extraction_model = extraction_model
        self._classification_model = classification_model

    async def extract(self, text: str, doc_type: str | None) -> ExtractionOutcome:
        resolved_doc_type = await self._resolve_doc_type(text, doc_type)
        entry = DOC_TYPE_REGISTRY[resolved_doc_type]
        system_prompt = _build_extraction_system_prompt(entry.system_prompt, entry.model)

        messages: list[dict[str, Any]] = [{"role": "user", "content": text}]
        last_error: ValidationError | None = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            content = await call_llm(self._client, self._extraction_model, system_prompt, messages)
            try:
                data = entry.model.model_validate_json(strip_code_fences(content))
                return ExtractionOutcome(doc_type=resolved_doc_type, data=data)
            except ValidationError as exc:
                last_error = exc
                if attempt >= MAX_ATTEMPTS:
                    break
                repair_prompt = (
                    "Your previous response failed validation with these errors:\n"
                    f"{_format_validation_errors(exc)}\n\n"
                    "Please re-extract the full JSON object from the original text below, "
                    "correcting only the fields mentioned above. Respond with ONLY the JSON object.\n\n"
                    f"Original text:\n{text}"
                )
                messages = [{"role": "user", "content": repair_prompt}]

        assert last_error is not None
        raise ExtractionFailedError(resolved_doc_type, last_error, MAX_ATTEMPTS)

    async def _resolve_doc_type(self, text: str, doc_type: str | None) -> str:
        if doc_type is not None:
            if doc_type not in DOC_TYPE_REGISTRY:
                raise UnknownDocTypeError(doc_type)
            return doc_type
        classified = await classify_doc_type(self._client, self._classification_model, text)
        if classified not in DOC_TYPE_REGISTRY:
            raise UnknownDocTypeError(classified)
        return classified
