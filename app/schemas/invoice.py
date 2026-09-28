from datetime import date
from decimal import Decimal

from typing import ClassVar

from pydantic import BaseModel, model_validator

INVOICE_SYSTEM_PROMPT = (
    "You extract structured invoice data from unstructured text (emails, scanned "
    "invoice OCR output, plain-text invoices, etc.). Extract every line item you can "
    "find. All monetary amounts must be plain decimal numbers (no currency symbols or "
    "thousands separators). If a field is genuinely absent from the text, omit it "
    "only if it is optional; never invent values. total_amount must equal the sum of "
    "each line item's line_total plus tax_amount."
)


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: Decimal
    line_total: Decimal


class Invoice(BaseModel):
    vendor_name: str
    vendor_address: str | None = None
    invoice_number: str
    invoice_date: date
    due_date: date | None = None
    line_items: list[LineItem]
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total_amount: Decimal
    currency: str = "USD"
    payment_terms: str | None = None

    _TOTAL_TOLERANCE: ClassVar[Decimal] = Decimal("0.01")

    @model_validator(mode="after")
    def check_total(self) -> "Invoice":
        computed = sum((li.line_total for li in self.line_items), Decimal("0")) + self.tax_amount
        if abs(computed - self.total_amount) > self._TOTAL_TOLERANCE:
            raise ValueError(
                f"total_amount ({self.total_amount}) does not equal the sum of line "
                f"item totals plus tax ({computed})"
            )
        return self
