from unittest.mock import AsyncMock

import httpx2
import openai
import pytest
from pydantic import ValidationError

from app.exceptions import ExtractionFailedError, LLMServiceError, UnknownDocTypeError
from app.schemas.invoice import Invoice
from app.services.extraction import ExtractionService
from tests.conftest import make_parsed_response

VALID_INVOICE = Invoice(
    vendor_name="Acme Corp",
    invoice_number="INV-001",
    invoice_date="2026-01-01",
    line_items=[{"description": "Widget", "quantity": 2, "unit_price": "10.00", "line_total": "20.00"}],
    subtotal="20.00",
    tax_amount="2.00",
    total_amount="22.00",
)

# A raw dict that satisfies Invoice's field types but fails the custom total-check validator.
BAD_TOTAL_PAYLOAD = {
    "vendor_name": "Acme Corp",
    "invoice_number": "INV-001",
    "invoice_date": "2026-01-01",
    "line_items": [{"description": "Widget", "quantity": 2, "unit_price": "10.00", "line_total": "20.00"}],
    "subtotal": "20.00",
    "tax_amount": "2.00",
    "total_amount": "999.00",
}


def make_service(mock_client) -> ExtractionService:
    return ExtractionService(
        client=mock_client,
        extraction_model="meta-llama/llama-3.3-70b-instruct:free",
        classification_model="qwen/qwen-2.5-72b-instruct:free",
    )


@pytest.mark.asyncio
async def test_extract_succeeds_first_try():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = make_parsed_response(VALID_INVOICE)

    service = make_service(mock_client)
    outcome = await service.extract("some invoice text", doc_type="invoice")

    assert outcome.doc_type == "invoice"
    assert outcome.data.total_amount == VALID_INVOICE.total_amount
    assert mock_client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_extract_repairs_after_validation_error():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        make_parsed_response(BAD_TOTAL_PAYLOAD),
        make_parsed_response(VALID_INVOICE),
    ]

    service = make_service(mock_client)
    outcome = await service.extract("some invoice text", doc_type="invoice")

    assert outcome.data.total_amount == VALID_INVOICE.total_amount
    assert mock_client.chat.completions.create.await_count == 2

    second_call_kwargs = mock_client.chat.completions.create.await_args_list[1].kwargs
    repair_content = second_call_kwargs["messages"][-1]["content"]
    assert "total_amount" in repair_content or "check_total" in repair_content


@pytest.mark.asyncio
async def test_extract_raises_after_exhausting_retries():
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        make_parsed_response(BAD_TOTAL_PAYLOAD),
        make_parsed_response(BAD_TOTAL_PAYLOAD),
    ]

    service = make_service(mock_client)
    with pytest.raises(ExtractionFailedError) as exc_info:
        await service.extract("some invoice text", doc_type="invoice")

    assert exc_info.value.attempt_count == 2
    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_unknown_doc_type_raises_without_calling_llm():
    mock_client = AsyncMock()
    service = make_service(mock_client)

    with pytest.raises(UnknownDocTypeError):
        await service.extract("some text", doc_type="not_a_real_type")

    mock_client.chat.completions.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_rate_limit_error_maps_to_llm_service_error():
    mock_client = AsyncMock()
    request = httpx2.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response = httpx2.Response(429, request=request)
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        "rate limited", response=response, body=None
    )

    service = make_service(mock_client)
    with pytest.raises(LLMServiceError) as exc_info:
        await service.extract("some invoice text", doc_type="invoice")

    assert exc_info.value.status_code == 503
    assert mock_client.chat.completions.create.await_count == 1


@pytest.mark.asyncio
async def test_empty_choices_response_maps_to_llm_service_error():
    from types import SimpleNamespace

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(choices=[])

    service = make_service(mock_client)
    with pytest.raises(LLMServiceError) as exc_info:
        await service.extract("some invoice text", doc_type="invoice")

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_connection_error_maps_to_llm_service_error():
    mock_client = AsyncMock()
    request = httpx2.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    mock_client.chat.completions.create.side_effect = openai.APIConnectionError(request=request)

    service = make_service(mock_client)
    with pytest.raises(LLMServiceError) as exc_info:
        await service.extract("some invoice text", doc_type="invoice")

    assert exc_info.value.status_code == 503
