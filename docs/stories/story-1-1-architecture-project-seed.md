# Story 1.1 — Architecture, LangChain project seed, and Open WebUI connection

## Purpose

Start the **Learning Companion Chatbot**, the capstone for a short, beginner LangChain and LangGraph classroom course. This story records the architecture, gets the instructor's approval, and then seeds a small LangChain-backed chat service. The participant's existing Open WebUI uses that service to show one real Grok reply.

## What this story implements in plain English

After this story, a participant can:

- Start a small local chat application with one command.
- Point their existing Open WebUI at it and pick the model it lists.
- Send a greeting and a simple study question, and see a Grok answer appear in Open WebUI.
- Read a one-page note showing how a message travels from Open WebUI to the answer and back.
- Keep their real API key in a private `.env` file that is never committed.

## Prerequisites

- Python 3.12 and UV are installed.
- Open WebUI is already installed and working. It is the supplied chat client only. **Do not reinstall, reconfigure, modify, or build it.**
- The instructor has supplied the Grok model name. The participant has a Grok API key.
- Resolve the project path first. Read `docs/config.yaml` if it exists, then `docs/architecture.md` if present, the repository layout, and existing stories. Use a configured project path when one exists; otherwise use the repository root. Preserve existing work.

## Work to do

### Step 1 — Architecture first (stop for approval)

1. Create or update `docs/architecture.md`. Keep it short and plain. Record this single classroom flow:

   `Open WebUI → this local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI`

2. Also record:
   - Open WebUI is already installed and working. It is the chat client only, and participants do not reinstall, reconfigure, modify, or build it.
   - The capstone is a small **Learning Companion Chatbot**, not a custom frontend or a second demonstration application.
   - API keys stay in an untracked `.env`.
   - Application instructions stay separate from user messages.
   - Out of scope: authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, and extensive tests.
   - A short note comparing a direct Python API call with this LangChain flow, covering what LangChain now organises (prompt construction, message formats, provider client, response handling).
3. **Stop and ask the instructor to approve `docs/architecture.md`.** Before approval, do not create seed files, install dependencies, or scaffold code. Resume this same story only after explicit approval.

### Step 2 — Seed the project (only after approval)

1. Create a Python 3.12 and UV project containing:
   - `src/learning_companion/` (application package)
   - `tests/`
   - `.env.example`
   - `.gitignore` (must exclude `.env`)
   - `pyproject.toml`
   - `uv.lock`
   - `README.md`
2. Dependencies: FastAPI, Pydantic settings, `langchain`, the Grok-compatible LangChain provider integration, Uvicorn, Ruff, and a minimal test runner. Nothing else.
3. `.env.example` uses exactly these setting names:

   ```
   APP_ENV=development
   GROK_API_KEY=
   GROK_API_BASE_URL=https://api.x.ai/v1
   GROK_MODEL_NAME=
   HOST=127.0.0.1
   PORT=8000
   ```

   - `GROK_API_KEY` and `GROK_MODEL_NAME` stay blank.
   - Document in `README.md` that the instructor supplies the model name and participants put their real key only in untracked `.env`.
   - Add no Claude, alternate-provider, database, or production configuration.
4. The application must **start without a real API key**. It returns an honest configuration error only when a model call is attempted.

### Step 3 — Minimal FastAPI application

Implement exactly three routes:

- `GET /health`
- `GET /v1/models`: exposes the configured Grok model as the model Open WebUI can select.
- `POST /v1/chat/completions`: accepts the normal OpenAI-compatible request shape needed by Open WebUI: `model`, a list of text messages with roles `system`, `user`, or `assistant`, and `stream`.
  - `stream: false` returns normal OpenAI-compatible JSON.
  - `stream: true` returns normal text-only OpenAI-compatible SSE chunks, then a stop chunk, then `[DONE]`.

Do not create custom Open WebUI events, a second chat route, or a custom browser UI.

### Step 4 — One small LangChain flow

- Build one **prompt → Grok chat model → text output** flow with a fixed Learning Companion system instruction and the latest user message.
- Keep the system instruction and model name in one clear location, separate from the user message. Never place a real API key in the repository.
- Use this same flow behind the chat endpoint for both normal and streaming requests.
- Keep it deliberately small. Full prompt construction and conversation history belong to Story 2.1.
- Do not add a broad test suite, tool calls, LangGraph, agents, MCP, or advanced streaming features.

## Completion checks

Run only lightweight checks, and report the commands you actually ran:

1. Format and lint the changed code (for example `uv run ruff format` and `uv run ruff check`).
2. Start the API (for example `uv run uvicorn learning_companion.main:app --host 127.0.0.1 --port 8000`). It starts with an empty `GROK_API_KEY`.
3. `GET /health` returns OK.
4. `GET /v1/models` lists the configured Grok model.
5. With the real key in `.env`, make one **normal** and one **streaming** request through the existing Open WebUI setup.
   - If the connection needs a local base URL (for example `http://127.0.0.1:8000/v1`) or a model selection, document only that application-side connection value. Do not alter Open WebUI itself.
6. Run one prepared greeting and one simple study question in Open WebUI.

**Expected result:** one Grok reply visible in Open WebUI for each, streamed and not streamed. `docs/architecture.md` is approved and matches what was built.

## Handover

**Files created or changed:**

- `docs/architecture.md`
- `pyproject.toml`, `uv.lock`
- `.env.example`, `.gitignore`, `README.md`
- `src/learning_companion/` (settings, FastAPI app, the prompt → model → text flow)
- `tests/` (placeholder only, plus at most a minimal smoke check)

**What Story 2.1 will extend:** the same chat endpoint, Open WebUI connection, architecture note, and configuration. It replaces the fixed prompt with a reusable chat prompt (system message, previous messages, current message), refines the same chain, and adds a short in-memory conversation history with a readable development view of the prompt messages.
