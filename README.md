# AI Support Chatbot & Agent Dashboard 🤖

A portfolio-ready customer-support application built with **Python, Flask and SQLite**, with optional **OpenAI** and **Anthropic Claude** integrations, an agent dashboard, automated testing, Docker support and an incoming webhook designed for business automation workflows.

## 🚀 Live Demo

👉 https://ai-support-chatbot-lsvm.onrender.com

**Demo agent login**
- Email: `admin@demo.local`
- Password: `demo1234`

## Why this project

This demo goes beyond a chatbot UI. It demonstrates backend architecture, REST endpoints, authentication, SQL persistence, LLM-provider abstraction, operational workflows and integration patterns that can connect with tools such as **Make.com, Zapier, Shopify, WooCommerce, CRM systems or Telegram**.

## Features

- Public support chat UI
- Persistent conversations and messages in SQLite
- REST endpoints for conversation creation and chat
- Agent login with hashed passwords
- Agent dashboard with conversation metrics
- Conversation transcript view
- Status workflow: `open`, `needs_human`, `closed`
- Conversation source tracking (`web`, `webhook`, etc.)
- AI provider abstraction:
  - `mock` — works without an API key
  - `openai` — optional OpenAI API integration
  - `anthropic` — optional Claude API integration
- Incoming business-automation webhook
- Optional webhook-secret authentication
- Human-handoff detection
- Automated tests with `pytest`
- GitHub Actions CI
- Docker support
- `/health` endpoint for deployment checks
- Responsive custom CSS

## Tech stack

`Python` · `Flask` · `SQLite` · `HTML` · `CSS` · `JavaScript` · `REST API` · `Anthropic Claude` · `OpenAI` · `pytest` · `GitHub Actions` · `Docker`

## Architecture

```text
Customer / External System
        │
        ├── Web Chat
        │      │
        │      ▼
        └── Webhook API ───────┐
                               ▼
                         Flask Backend
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
              SQLite      AI Provider     Agent Dashboard
                              Layer
                         ┌─────┼─────┐
                         ▼     ▼     ▼
                       Mock OpenAI Claude
```

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/conversations` | Start a conversation |
| `POST` | `/api/chat` | Send a user message and receive AI response |
| `GET` | `/api/conversations/<id>/messages` | Fetch transcript |
| `POST` | `/api/webhooks/incoming` | Receive a message from an automation/integration |
| `GET` | `/health` | Service health check |

## Automation webhook

The incoming webhook allows an external automation system to send customer messages directly into the chatbot workflow.

Example payload:

```json
{
  "visitor_name": "Demo Customer",
  "source": "woocommerce",
  "message": "I need help with order #1024"
}
```

Example request:

```bash
curl -X POST http://127.0.0.1:5000/api/webhooks/incoming \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: change-this-webhook-secret" \
  -d '{"visitor_name":"Demo Customer","source":"make.com","message":"I need support"}'
```

This endpoint can be connected to flows such as:

```text
Shopify / WooCommerce / Website Form
              ↓
        Make.com / Zapier
              ↓
       Incoming Webhook
              ↓
         AI Assistant
              ↓
     Automated Reply / Human Handoff
```

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Docker

```bash
docker build -t ai-support-chatbot .
docker run -p 5000:5000 \
  -e SECRET_KEY=change-me \
  -e AI_PROVIDER=mock \
  ai-support-chatbot
```

## Enable Claude

```bash
export AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY="your-key"
python app.py
```

## Enable OpenAI

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY="your-key"
python app.py
```

If a configured AI service is unavailable, the application falls back safely to demo responses.

## Tests

```bash
pip install pytest
pytest -q
```

Tests cover health checks, conversation creation, chatbot responses, validation and missing conversations. GitHub Actions runs the test suite automatically on pushes and pull requests to `main`.

## Security notes

- API keys and secrets are configured through environment variables.
- `.env` files are excluded from Git.
- The webhook can be protected with `WEBHOOK_SECRET` and the `X-Webhook-Secret` header.
- Demo credentials are intentionally public and should be replaced in production.

## Production improvements

For a full production deployment I would add PostgreSQL, CSRF protection, rate limiting, role-based permissions, database migrations, background jobs, structured logging, observability and more advanced provider retry/error handling.

## Portfolio focus

This project demonstrates practical experience with **Python backend development, REST APIs, AI integrations, chatbot workflows, webhooks, business automation, testing, CI and containerization** — the same building blocks used in real automation and AI-agent projects.
