# Automated Multi-Platform Posting System

A high-performance FastAPI service that validates and publishes short messages across multiple third-party social networks, messaging webhooks, developer portals, and LLM platforms concurrently.

Built for the **Python Practical Test** (Chivox AI / Dxora Technologies).

---

## Architecture & Platform Integrations

The service exposes a single endpoint: `POST /posting`. When a message is submitted, the platform internally handles all platform selection and broadcasts to **9 integrated platforms** in parallel using `asyncio.gather`. 

Each platform is executed in total isolation; an authentication failure, network error, or timeout on one platform never halts or affects the others.

| Platform | Category | Official API Documentation | Public Link? | Required Credentials |
|---|---|---|:---:|---|
| **dpaste** | Pastebin Utility | https://dpaste.com/api/v2/ | Yes | *None (zero-config live demo)* |
| **Telegram** | Messaging / Bots | https://core.telegram.org/bots/api#sendmessage | Yes (if channel) | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| **Discord** | Team Messaging | https://discord.com/developers/docs/resources/webhook | No (private guild) | `DISCORD_WEBHOOK_URL` |
| **Slack** | Team Messaging | https://api.slack.com/messaging/webhooks | No (private workspace) | `SLACK_WEBHOOK_URL` |
| **Mastodon** | Fediverse / Social | https://docs.joinmastodon.org/methods/statuses/ | Yes | `MASTODON_INSTANCE_URL`, `MASTODON_ACCESS_TOKEN` |
| **GitHub Gist** | Developer Services | https://docs.github.com/en/rest/gists/gists | Yes | `GITHUB_TOKEN` (gist scope) |
| **Bluesky** | AT Protocol Social | https://docs.bsky.app/docs/api/com-atproto-repo-create-record | Yes | `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` |
| **Hugging Face** | LLM Platform | https://huggingface.co/docs/huggingface_hub/guides/community | Yes | `HF_TOKEN`, `HF_REPO_ID` |
| **Dev.to** | Developer Articles | https://developers.forem.com/api/v1#tag/articles/operation/createArticle | Yes | `DEVTO_API_KEY` |

> **Live Demo Highlight:** Because `dpaste` requires zero API credentials, running the service out of the box will immediately post to dpaste and return a live, public, clickable URL alongside clean missing-credential reports for unconfigured platforms.

---

## Project Structure

```text
automated-posting/
├── app/
│   ├── main.py                  # FastAPI application, exception handlers & routing
│   ├── schemas.py               # Pydantic v2 validation models & response envelope
│   ├── config.py                # Environment configuration & cached settings
│   ├── platforms/               # Platform adapter implementations
│   │   ├── __init__.py
│   │   ├── base.py              # BasePlatform abstract class & error normalization
│   │   ├── bluesky.py           # AT Protocol (createSession + createRecord)
│   │   ├── devto.py             # Dev.to articles API
│   │   ├── discord.py           # Discord webhook with ?wait=true
│   │   ├── dpaste.py            # Zero-credential live public paste API
│   │   ├── github_gist.py       # GitHub REST API v3 Gists
│   │   ├── huggingface.py       # Hugging Face LLM discussions API
│   │   ├── mastodon.py          # Fediverse statuses API
│   │   ├── slack.py             # Slack incoming webhooks
│   │   └── telegram.py          # Telegram Bot API with channel detection
│   └── services/
│       ├── __init__.py
│       └── posting_service.py   # Asynchronous multi-platform orchestrator
├── logs/
│   └── posting.log              # JSON-lines execution audit trail
├── screenshots/
│   └── swagger.png              # Swagger UI documentation capture
├── tests/
│   ├── __init__.py
│   ├── test_platforms.py        # Isolated platform tests with mocked HTTP transport
│   ├── test_posting.py          # Orchestration, error mapping & fault tolerance
│   └── test_validation.py       # Pydantic validation & HTTP 400 error handlers
├── .env.example                 # Template for platform credentials
├── .gitignore                   # Excludes .env, virtualenv, and test cache
├── pytest.ini                   # Async test runner configuration
├── requirements.txt             # Project dependencies
├── sample_output.json           # Sample successful API response
├── sample_validation.json       # Sample validation error response
└── README.md
```

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12 and 3.13)
- pip

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

You can optionally populate any API keys you possess in `.env`. Any unconfigured platform safely defaults to a `failed` status with a descriptive `"Missing credentials: ..."` error.

---

## Running the Application

Start the local server using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000
```

- **Interactive API Documentation (Swagger UI):** http://localhost:4000/docs
- **Alternative Documentation (ReDoc):** http://localhost:4000/redoc
- **Health Check Endpoint:** http://localhost:4000/

### Swagger UI Preview

![Swagger UI](screenshots/swagger.png)

---

## API Usage & Examples

### Endpoint
```http
POST http://localhost:4000/posting
Content-Type: application/json
```

### Request Rules & Validation
- **Maximum length:** 200 characters.
- **CTA link requirement:** Exactly one valid `http://` or `https://` CTA URL must be present in the message.
- **URL structure:** The link must contain a valid domain (e.g. `https://example.com`).
- **Internal platform selection:** Handled automatically; client cannot pass a platform filter.

### Sample Request (cURL)

```bash
curl -X POST http://localhost:4000/posting \
  -H "Content-Type: application/json" \
  -d '{"message": "Check out our latest business platform and grow your online visibility. https://example.com"}'
```

### Sample Success Response (HTTP 200)

```json
{
  "success": true,
  "results": [
    {
      "platform": "Telegram",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing credentials: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"
    },
    {
      "platform": "Discord",
      "status": "failed",
      "posted_url": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Missing credentials: DISCORD_WEBHOOK_URL"
    },
    {
      "platform": "dpaste",
      "status": "success",
      "posted_url": "https://dpaste.com/FN9PA7MQL",
      "public_access": true,
      "date": "2026-11-16",
      "time": "12:03:31",
      "error": null
    }
  ]
}
```

*Note: Overall `success` is `true` as long as at least one platform successfully posts.*

### Sample Validation Failure (HTTP 400)

When an invalid message is submitted (e.g. Missing CTA link, exceeding 200 characters, or invalid URL structure):

```json
{
  "success": false,
  "error": "Exactly one CTA link must be included in the message.",
  "results": []
}
```

---

## Running the Automated Test Suite

The test suite contains **29 unit and integration tests** testing validation rules, fault isolation, timeout mappings, authentication error mappings, and platform payloads using mocked HTTP transports:

```bash
pytest -v
```

All tests execute completely offline without live external dependencies.
