# Learning Companion Chatbot

A small LangChain and LangGraph chat service that your existing Open WebUI connects to.

`Open WebUI → /v1/chat/completions → LangGraph (router → answer → reviewer → improver) → Grok model → answer`

See [docs/architecture.md](docs/architecture.md).

## What it does

- A normal message is answered by the **general-chat** chain.
- A message that starts with `/study`, for example `/study Explain what an API is`, is answered by the **study helper**: a short explanation, a small example, and one next step.
- Each reply starts with `[route: general]` or `[route: study]` so you can see which path was used.
- A **reviewer** checks the draft once. If it needs work, an **improver** rewrites it once, and the reviewer checks again. It never improves more than once.
- Replies stream into Open WebUI as the model writes them.

The server log shows a compact trace for each request, for example `route=study | review=approve | revisions=0 | START → router → study_helper → reviewer → END`. It never logs keys or message text.

## Setup

1. Copy `.env.example` to `.env`.
2. Put your real Grok key in `GROK_API_KEY` and the model name from your instructor in `GROK_MODEL_NAME`. `.env` is never committed.
3. Run: `uv run learning-companion` (serves on `http://127.0.0.1:8000`).

If `uv` is not on your PATH, use `python -m uv run learning-companion`, or start the app with the project's own Python:

```
.\.venv\Scripts\python.exe -m uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000
```

## Connect Open WebUI

In your existing Open WebUI, point its OpenAI-compatible connection at `http://127.0.0.1:8000/v1` (any API key value works), then select the model listed by `/v1/models`. If Open WebUI runs in Docker, use `http://host.docker.internal:8000/v1`. Open WebUI itself is not modified.

Opening `http://127.0.0.1:8000/` in a browser shows "Not Found". That is normal: the app only has `/health`, `/v1/models` and `/v1/chat/completions`.

## Try the study helper without Open WebUI

```
uv run python -m learning_companion.dev_study "Explain what an API is"
```

## Settings

- The speed of the streamed text is `STREAM_DELAY_SECONDS` in `src/learning_companion/main.py`. Raise it to slow the reply down, lower it to speed it up.
- The number of earlier messages used as history is `MAX_HISTORY_MESSAGES` in `src/learning_companion/chain.py`.

## Checks

```
uv run ruff format
uv run ruff check
uv run pytest
```

The app starts without a key; it returns a configuration error only when a chat is attempted.
