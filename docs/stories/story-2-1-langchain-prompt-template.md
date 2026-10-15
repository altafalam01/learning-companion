# Story 2.1 — LangChain prompt template

## Purpose

Make the seed's LangChain flow reusable and easy to understand. The fixed prompt becomes a small chat prompt with two clearly separate parts: the application's Learning Companion instruction and the user's current message. The chat endpoints, Grok settings and Open WebUI connection stay exactly as they are.

## What this story implements in plain English

- The chatbot's role and rules live in one place and are kept apart from what the user types.
- A user cannot replace the chatbot's role by sending their own "system" text. It is treated as ordinary user content.
- The participant sees no change in Open WebUI. Answers still arrive the same way, streamed or not.
- A short development log shows who said what (roles and counts) so the flow can be inspected.

## Prerequisites

- Story 1.1 is complete and the app answers through Open WebUI.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Story 1.1, the existing code, `.env.example`, and the OpenAI-compatible chat adapter.
- Preserve existing work, routes, settings and the working Open WebUI connection.

## Work to do

1. **Replace the fixed prompt** with a small LangChain chat prompt built from LangChain message and prompt-template classes. It has two parts:
   - a stable Learning Companion system instruction owned by the application;
   - the current user message.

   Do not concatenate a large ad-hoc string.
2. **Use only the latest supported user message** from the OpenAI-compatible request.
   - A request-supplied `system` message is user-provided content. It must never replace the application's instruction.
   - Do not handle history yet. Story 2.2 adds it.
3. **Keep one chain.** The existing prompt → Grok model → text-output chain serves both the normal and streaming paths.
4. **Keep the API unchanged.** `GET /health`, `GET /v1/models` and `POST /v1/chat/completions` keep the same normal JSON and SSE behaviour. Add no custom message formats or Open WebUI plugins.
5. **Add a compact development-only log or helper** showing message roles and counts. It must never show API keys or the full hidden instruction.
6. **Update `docs/architecture.md`** with the message flow (system instruction, then current user message, then model, then answer) and the deliberate no-persistence boundary.

Out of scope: a command-line-only chatbot, a second chat path, conversation history, a database, persistent memory, RAG, tools, MCP, LangGraph, a new frontend.

## Completion checks

Run only:

1. Format and lint (`python -m uv run ruff format` and `python -m uv run ruff check`).
2. Start the app and ask one ordinary question in the existing Open WebUI chat.
3. In the development log, confirm the roles reach the prompt in the expected order (system, then user).

**Expected result:** Open WebUI still renders the Grok answer, with no visible change. Do not add an evaluation harness, broad test suite, production memory or security programme.

## Handover

**Files changed:** `src/learning_companion/chain.py` (prompt template), the chat adapter in `src/learning_companion/main.py` (latest-user-message selection, role log), `docs/architecture.md`. Commands run are the lint and start commands above.

**Story 2.2 extends:** the same prompt with a place for earlier messages, so a follow-up question can use the conversation so far.
