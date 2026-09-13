# AI Support Chatbot & Agent Dashboard

A portfolio-ready customer-support application built with **Python, Flask and SQLite**. It includes a public chat widget, persistent conversation history, agent authentication, an operations dashboard, human-handoff statuses and an AI provider abstraction that can run in demo mode or connect to **OpenAI** / **Anthropic Claude**.

## Why this project

This demo shows more than a chatbot UI: it demonstrates backend logic, REST endpoints, authentication, SQL persistence, third-party API integration patterns and a small operational dashboard.

## Features

- Public support chat UI
- Persistent conversations and messages in SQLite
- REST endpoints for conversation creation and chat
- Agent login with hashed passwords
- Agent dashboard with conversation metrics
- Conversation transcript view
- Status workflow: `open`, `needs_human`, `closed`
- AI provider abstraction:
  - `mock` — works without any API key
  - `openai` — optional OpenAI API
  - `anthropic` — optional Claude API
- `/health` endpoint for deployment checks
- Responsive custom CSS, no UI framework required

## Tech stack

`Python` · `Flask` · `SQLite` · `HTML` · `CSS` · `JavaScript` · `REST API` · `Werkzeug Auth`

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

### Demo agent account

```text
Email: admin@demo.local
Password: demo1234
```

## Enable a real AI provider

Copy the example environment configuration:

```bash
cp .env.example .env
```

Export the variables in your shell (or load them with your preferred environment manager).

### Claude

```bash
export AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY="your-key"
python app.py
```

### OpenAI

```bash
export AI_PROVIDER=openai
export OPENAI_API_KEY="your-key"
python app.py
```

If the API is unavailable, the application safely falls back to demo responses.

## Main API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/conversations` | Start a conversation |
| `POST` | `/api/chat` | Send a user message and receive AI response |
| `GET` | `/api/conversations/<id>/messages` | Fetch transcript |
| `GET` | `/health` | Service health check |

## Example request

```bash
curl -X POST http://127.0.0.1:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{"visitor_name":"Demo Client"}'
```

Then:

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":1,"message":"Care este programul?"}'
```

## Architecture

```text
Browser UI
   │
   ├── Public Chat ──> Flask REST API ──> SQLite
   │                         │
   │                         └── AI Provider Layer
   │                              ├── Mock
   │                              ├── OpenAI
   │                              └── Anthropic Claude
   │
   └── Agent Login ──> Dashboard / Conversation Review
```

## Production improvements

For a real deployment I would add PostgreSQL, CSRF protection, rate limiting, role-based permissions, migrations, background jobs/webhooks, observability, Docker and automated tests/CI.

## Portfolio note

This project is intentionally structured so an interviewer can run it without an external AI account, while the integration layer shows how a production LLM provider can be connected through environment variables.
