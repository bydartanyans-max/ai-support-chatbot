# Interview talking points

- I separated AI-provider logic from the Flask routes so providers can be switched without rewriting business logic.
- The app runs without paid API access using a deterministic mock provider, which makes demos reliable.
- Conversation data is persisted in SQL rather than browser memory.
- Passwords are hashed with Werkzeug; plaintext passwords are not stored.
- Human handoff is modeled as a conversation status instead of being hard-coded into the UI.
- A production version would use PostgreSQL + migrations + Docker + CI + rate limiting.
