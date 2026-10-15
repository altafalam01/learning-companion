# Learning Companion Chatbot

A small LangChain-backed chat service that your existing Open WebUI connects to.

`Open WebUI → /v1/chat/completions → LangChain prompt + Grok model → answer`

See [docs/architecture.md](docs/architecture.md).

## Setup

1. Copy `.env.example` to `.env`.
2. Put your real Grok key in `GROK_API_KEY` and the model name from your instructor in `GROK_MODEL_NAME`. `.env` is never committed.
3. Run: `uv run learning-companion` (serves on `http://127.0.0.1:8000`).

## Connect Open WebUI

In your existing Open WebUI, point its OpenAI-compatible connection at `http://127.0.0.1:8000/v1` (any API key value works), then select the model listed by `/v1/models`. If Open WebUI runs in Docker, use `http://host.docker.internal:8000/v1`. Open WebUI itself is not modified.

## Checks

```
uv run ruff format
uv run ruff check
uv run pytest
```

The app starts without a key; it returns a configuration error only when a chat is attempted.
