# parse-unstructured-text

A FastAPI microservice that turns unstructured text (invoices, customer support tickets)
into validated, type-safe JSON using an LLM, and persists the results to PostgreSQL.

- Text goes in, either with an explicit `doc_type` or none (the service classifies it automatically).
- The LLM's output is validated against a Pydantic schema, with an automatic repair retry if validation fails.
- Every parse attempt (successful or failed) is persisted, and past results can be listed/fetched later.
- All endpoints are protected by a shared `X-API-Key` header.

## Requirements

- Docker and Docker Compose
- An [OpenRouter](https://openrouter.ai/) API key (free-tier models are used by default)

## Setup

1. Clone the repo and copy the example environment file:

   ```bash
   git clone https://github.com/Chaitanya0076/parse-unstructured-text.git
   cd parse-unstructured-text
   cp .env.example .env
   ```

2. Edit `.env` and fill in your own values:

   | Variable | Description |
   |---|---|
   | `OPENROUTER_API_KEY` | Your OpenRouter API key — get one at [openrouter.ai/keys](https://openrouter.ai/keys) |
   | `OPENROUTER_BASE_URL` | Leave as `https://openrouter.ai/api/v1` unless you're proxying it |
   | `DATABASE_URL` | Leave as the default `postgres` service URL unless you're using an external database |
   | `API_KEY` | A secret of your own choosing — this is what callers must send as `X-API-Key` to use the API |
   | `EXTRACTION_MODEL` / `CLASSIFICATION_MODEL` | OpenRouter model slugs. Any [free-tier model](https://openrouter.ai/models?max_price=0) that supports instruction following works |

3. Build and start the service (this also runs database migrations automatically):

   ```bash
   docker compose up -d --build
   ```

4. Confirm it's up:

   ```bash
   curl http://localhost:8000/healthz
   ```

## Usage

All endpoints below require an `X-API-Key` header matching the `API_KEY` value in your `.env`.

### Parse text into structured JSON

```bash
curl -X POST http://localhost:8000/v1/parse \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your API_KEY>" \
  -d '{
    "text": "Invoice #INV-001 from Acme Corp, dated 2026-01-01. 2x Widget @ $10.00 = $20.00. Subtotal $20.00, tax $2.00, total $22.00.",
    "doc_type": "invoice"
  }'
```

`doc_type` is optional — omit it and the service will classify the text automatically.

### List supported document types and their schemas

```bash
curl http://localhost:8000/v1/schemas -H "X-API-Key: <your API_KEY>"
```

### Fetch a previously parsed document

```bash
curl http://localhost:8000/v1/documents/<document-id> -H "X-API-Key: <your API_KEY>"
```

### List parsed documents

```bash
curl "http://localhost:8000/v1/documents?doc_type=invoice&status=completed&limit=20&offset=0" \
  -H "X-API-Key: <your API_KEY>"
```

## Supported document types

- `invoice` — vendor invoices/bills
- `support_ticket` — customer support tickets

## Development

Run the test suite locally (uses an in-memory/mock LLM client, no real API calls or running containers needed):

```bash
pip install -e ".[dev]"
pytest
```

## Tech stack

FastAPI, Pydantic, SQLAlchemy (async) + Alembic, PostgreSQL, OpenRouter (OpenAI-compatible API), Docker Compose.
