from typing import Any

import openai
from openai import AsyncOpenAI

from app.exceptions import LLMServiceError


async def call_llm(
    client: AsyncOpenAI, model: str, system_prompt: str, messages: list[dict[str, Any]]
) -> str:
    try:
        response = await client.chat.completions.create(
            model=model,
            max_tokens=16000,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
    except openai.RateLimitError as exc:
        raise LLMServiceError(f"LLM API rate limited: {exc}", status_code=503) from exc
    except openai.APIConnectionError as exc:
        raise LLMServiceError(f"Could not reach LLM API: {exc}", status_code=503) from exc
    except openai.APIStatusError as exc:
        status = 503 if exc.status_code >= 500 else 502
        raise LLMServiceError(f"LLM API error ({exc.status_code}): {exc}", status_code=status) from exc
    if not response.choices:
        raise LLMServiceError("LLM API returned no completion choices", status_code=503)
    return response.choices[0].message.content or ""
