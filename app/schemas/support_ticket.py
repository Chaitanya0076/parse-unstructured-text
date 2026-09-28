from enum import Enum

from pydantic import BaseModel

TICKET_SYSTEM_PROMPT = (
    "You extract structured data from unstructured customer support text (emails, "
    "chat transcripts, submitted tickets). Infer priority and sentiment from tone and "
    "content if not explicitly stated. issue_category should be a short label such as "
    "'billing', 'technical', or 'account'. Never invent a customer name or email that "
    "is not present in the text."
)


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class SupportTicket(BaseModel):
    customer_name: str | None = None
    customer_email: str | None = None
    issue_category: str
    priority: Priority
    summary: str
    sentiment: Sentiment
    requested_action: str
    product_or_service: str | None = None
    order_or_account_id: str | None = None
