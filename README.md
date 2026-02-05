# Nexlayer — Secure AI Integration Gateway

Nexlayer is an enterprise middleware gateway that sits between your internal applications and AI model providers. It enforces compliance policies, detects sensitive data, controls access with RBAC, and produces a full audit trail for every AI interaction.

## Prerequisites

- Python 3.11+
- PostgreSQL 16 (or use the provided Docker Compose)
- Docker & Docker Compose (optional, for containerized deployment)

## Quick Start (Local Development)

### 1. Clone and install

```bash
git clone https://github.com/Leulyakot/Nexlayer.git
cd Nexlayer
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set the required values:

| Variable | Required | Description |
|---|---|---|
| `JWT_SECRET_KEY` | Yes | A strong random string for signing JWTs |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `OPENAI_API_KEY` | For OpenAI routing | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | For Anthropic routing | Your Anthropic API key |
| `API_KEYS` | Optional | Comma-separated list of valid API keys |

### 3. Start PostgreSQL

If you don't have a local PostgreSQL instance, start one with Docker:

```bash
docker run -d \
  --name nexlayer-postgres \
  -e POSTGRES_USER=nexlayer \
  -e POSTGRES_PASSWORD=nexlayer_secret \
  -e POSTGRES_DB=nexlayer \
  -p 5432:5432 \
  postgres:16-alpine
```

### 4. Run the server

```bash
uvicorn nexlayer.main:app --reload
```

The API is now available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

---

## Quick Start (Docker Compose)

This starts both the Nexlayer gateway and PostgreSQL in containers:

```bash
cp .env.example .env
# Edit .env with your credentials

cd docker
docker compose up --build
```

The API is available at `http://localhost:8000`.

---

## Usage

### Get a JWT token (development only)

The `/v1/auth/token` endpoint is available in `development` and `test` environments for generating test tokens:

```bash
curl -X POST "http://localhost:8000/v1/auth/token?username=admin&role=admin"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1...",
  "token_type": "bearer"
}
```

### Send an AI request

```bash
curl -X POST http://localhost:8000/v1/ai/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "user_id": "analyst-1",
    "model": "openai",
    "prompt": "Summarize the key points of our Q4 report",
    "metadata": {}
  }'
```

You can also authenticate with an API key instead of a JWT:

```bash
curl -X POST http://localhost:8000/v1/ai/request \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-api-key>" \
  -d '{
    "user_id": "analyst-1",
    "model": "anthropic",
    "prompt": "Summarize the key points of our Q4 report",
    "metadata": {}
  }'
```

### Health check

```bash
curl http://localhost:8000/health
```

---

## API Reference

### `POST /v1/ai/request`

Primary gateway endpoint. Every request goes through the full pipeline:

1. **Authentication** — JWT bearer token or `X-API-Key` header
2. **RBAC** — Verifies the caller's role has access to the requested model
3. **Policy enforcement** — Scans the prompt for sensitive data and content violations
4. **AI provider routing** — Forwards the (potentially redacted) prompt to OpenAI, Anthropic, or a local LLM
5. **Audit logging** — Records the interaction as structured JSON

**Request body:**

```json
{
  "user_id": "string",
  "model": "openai | anthropic | local",
  "prompt": "string",
  "metadata": {}
}
```

**Response:**

```json
{
  "request_id": "uuid",
  "model_provider": "openai",
  "response_text": "...",
  "policy_actions": [],
  "classification_results": [],
  "timestamp": "2026-02-05T12:00:00Z"
}
```

**Status codes:**

| Code | Meaning |
|---|---|
| 200 | Success |
| 401 | Missing or invalid authentication |
| 403 | Blocked by RBAC or policy enforcement |
| 429 | Rate limit exceeded |
| 502 | AI provider error |

### `POST /v1/auth/token`

Development-only token generator. Disabled in production.

### `GET /health`

Returns `{"status": "ok", "version": "0.1.0"}`.

---

## RBAC Roles

Access is controlled via three roles defined in `config/policies.yaml`:

| Role | Models | Max Tokens | Rate Limit (req/min) |
|---|---|---|---|
| `admin` | openai, anthropic, local | 8192 | 120 |
| `analyst` | openai, anthropic | 4096 | 60 |
| `viewer` | openai | 2048 | 30 |

---

## Policy Configuration

All policies are defined in `config/policies.yaml`. Changes take effect on the next request (no restart needed).

**Data protection** — PII patterns (email, SSN, phone, credit card, IP address) and CUI keywords are detected and either blocked or redacted before the prompt reaches the AI provider.

**Content classification** — Prompts containing prompt-injection attempts or harmful content keywords are blocked.

**Compliance** — Audit logging is mandatory; prompt hashes and response metadata are recorded with a configurable retention period.

---

## Running Tests

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

To run with coverage:

```bash
pytest --cov=nexlayer
```

---

## Project Structure

```
nexlayer/
  api/            API gateway (routes, middleware)
  auth/           JWT, API key auth, RBAC
  audit/          Structured audit logging
  config/         Settings and YAML policy loader
  core/           Pydantic schemas, structured logging
  database/       SQLAlchemy models and async sessions
  detection/      PII regex, CUI keyword, ML stub detectors
  policy/         Policy enforcement engine
  providers/      OpenAI, Anthropic, local LLM adapters
  telemetry/      OpenTelemetry tracing
  main.py         FastAPI application factory
config/
  policies.yaml   Externalized policy definitions
docker/
  Dockerfile      Production container image
tests/            Test suite (47 tests)
```

## License

MIT
