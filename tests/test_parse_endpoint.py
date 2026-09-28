import pytest

from app.schemas.invoice import Invoice
from app.schemas.support_ticket import Priority, Sentiment, SupportTicket
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

VALID_TICKET = SupportTicket(
    issue_category="billing",
    priority=Priority.high,
    summary="Customer was charged twice",
    sentiment=Sentiment.negative,
    requested_action="Refund the duplicate charge",
)


@pytest.mark.asyncio
async def test_parse_requires_api_key(client):
    response = await client.post("/v1/parse", json={"text": "some invoice text"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_parse_invoice_success(client, api_key_headers, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value = make_parsed_response(VALID_INVOICE)

    response = await client.post(
        "/v1/parse",
        json={"text": "Acme Corp invoice for a widget", "doc_type": "invoice"},
        headers=api_key_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["doc_type"] == "invoice"
    assert body["status"] == "completed"
    assert body["data"]["vendor_name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_parse_unknown_doc_type(client, api_key_headers):
    response = await client.post(
        "/v1/parse",
        json={"text": "some text", "doc_type": "not_a_real_type"},
        headers=api_key_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_parse_without_doc_type_classifies(client, api_key_headers, mock_llm_client):
    mock_llm_client.chat.completions.create.side_effect = [
        make_parsed_response({"doc_type": "support_ticket"}),
        make_parsed_response(VALID_TICKET),
    ]

    response = await client.post(
        "/v1/parse",
        json={"text": "I was charged twice, please refund me"},
        headers=api_key_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["doc_type"] == "support_ticket"
    assert mock_llm_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_parse_extraction_failure_returns_422(client, api_key_headers, mock_llm_client):
    bad_payload = {
        "vendor_name": "Acme Corp",
        "invoice_number": "INV-001",
        "invoice_date": "2026-01-01",
        "line_items": [
            {"description": "Widget", "quantity": 2, "unit_price": "10.00", "line_total": "20.00"}
        ],
        "subtotal": "20.00",
        "tax_amount": "2.00",
        "total_amount": "999.00",
    }
    mock_llm_client.chat.completions.create.side_effect = [
        make_parsed_response(bad_payload),
        make_parsed_response(bad_payload),
    ]

    response = await client.post(
        "/v1/parse",
        json={"text": "some invoice text", "doc_type": "invoice"},
        headers=api_key_headers,
    )

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["detail"] == "extraction_failed"
    assert body["attempt_count"] == 2
