import uuid

import pytest

from app.schemas.invoice import Invoice
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


@pytest.mark.asyncio
async def test_get_document_not_found(client, api_key_headers):
    response = await client.get(f"/v1/documents/{uuid.uuid4()}", headers=api_key_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_and_list_documents_after_parse(client, api_key_headers, mock_llm_client):
    mock_llm_client.chat.completions.create.return_value = make_parsed_response(VALID_INVOICE)

    created = await client.post(
        "/v1/parse",
        json={"text": "Acme Corp invoice", "doc_type": "invoice"},
        headers=api_key_headers,
    )
    document_id = created.json()["id"]

    get_response = await client.get(f"/v1/documents/{document_id}", headers=api_key_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == document_id

    list_response = await client.get("/v1/documents", params={"doc_type": "invoice"}, headers=api_key_headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] >= 1
    assert any(item["id"] == document_id for item in body["items"])


@pytest.mark.asyncio
async def test_documents_require_api_key(client):
    response = await client.get(f"/v1/documents/{uuid.uuid4()}")
    assert response.status_code == 401
