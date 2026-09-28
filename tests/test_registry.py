from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.registry import DOC_TYPE_REGISTRY
from app.schemas.invoice import Invoice
from app.schemas.support_ticket import Priority, Sentiment, SupportTicket


def test_registry_contains_expected_doc_types():
    assert set(DOC_TYPE_REGISTRY.keys()) == {"invoice", "support_ticket"}
    assert DOC_TYPE_REGISTRY["invoice"].model is Invoice
    assert DOC_TYPE_REGISTRY["support_ticket"].model is SupportTicket


def test_invoice_valid_totals():
    invoice = Invoice(
        vendor_name="Acme Corp",
        invoice_number="INV-001",
        invoice_date="2026-01-01",
        line_items=[
            {"description": "Widget", "quantity": 2, "unit_price": "10.00", "line_total": "20.00"}
        ],
        subtotal="20.00",
        tax_amount="2.00",
        total_amount="22.00",
    )
    assert invoice.total_amount == Decimal("22.00")


def test_invoice_rejects_mismatched_total():
    with pytest.raises(ValidationError):
        Invoice(
            vendor_name="Acme Corp",
            invoice_number="INV-001",
            invoice_date="2026-01-01",
            line_items=[
                {
                    "description": "Widget",
                    "quantity": 2,
                    "unit_price": "10.00",
                    "line_total": "20.00",
                }
            ],
            subtotal="20.00",
            tax_amount="2.00",
            total_amount="999.00",
        )


def test_support_ticket_valid():
    ticket = SupportTicket(
        issue_category="billing",
        priority=Priority.high,
        summary="Customer was charged twice",
        sentiment=Sentiment.negative,
        requested_action="Refund the duplicate charge",
    )
    assert ticket.priority is Priority.high
