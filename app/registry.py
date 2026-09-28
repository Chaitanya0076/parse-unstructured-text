from dataclasses import dataclass

from pydantic import BaseModel

from app.schemas.invoice import INVOICE_SYSTEM_PROMPT, Invoice
from app.schemas.support_ticket import TICKET_SYSTEM_PROMPT, SupportTicket


@dataclass(frozen=True)
class SchemaRegistryEntry:
    model: type[BaseModel]
    system_prompt: str
    description: str


DOC_TYPE_REGISTRY: dict[str, SchemaRegistryEntry] = {
    "invoice": SchemaRegistryEntry(
        model=Invoice,
        system_prompt=INVOICE_SYSTEM_PROMPT,
        description="Vendor invoices/bills",
    ),
    "support_ticket": SchemaRegistryEntry(
        model=SupportTicket,
        system_prompt=TICKET_SYSTEM_PROMPT,
        description="Customer support tickets",
    ),
}
