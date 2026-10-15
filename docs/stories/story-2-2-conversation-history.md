# Story 2.2 — Conversation history from Open WebUI

## Purpose

Let a follow-up question use earlier messages in the same chat. Open WebUI already sends the messages of the active chat with every request. This story passes a short, recent slice of them into the existing prompt template.

## What this story implements in plain English

- Ask a question, then ask "explain that more simply", and the chatbot knows what "that" means.
- Only the last few messages of the current chat are used. The limit is small and documented.
- Nothing is saved. When a request finishes, the app forgets it. A new chat starts fresh.
- A short development log shows the order of roles and the message count.

## Prerequisites

- Stories 1.1 and 2.1 are complete: the app answers through Open WebUI using the LangChain prompt template.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1 and 2.1, the existing code, `.env.example`, and the chat adapter.
- Preserve the endpoints, Grok configuration, prompt template, normal JSON/SSE behaviour and Open WebUI connection.

## Work to do

1. **Add a message placeholder** to the existing prompt template, between the application-owned system instruction and the latest user message. Use a LangChain message placeholder, not an ad-hoc string.
2. **Convert prior messages.** Turn supported earlier `user` and `assistant` messages from the request into LangChain messages, in their original order.
   - Ignore unsupported roles or content safely.
   - A request-supplied `system` message never replaces the application's stable instruction.
3. **Limit the history.** Use a small, documented maximum number of recent messages from the current request, held in one named constant.
4. **Keep one chain.** The same prompt → Grok model → text-output chain serves both normal and streaming replies. Request and response shapes do not change.
5. **Add a compact development log or helper** showing message roles and the message count. Never log API keys, the full hidden instruction, or large message bodies.
6. **Update `docs/architecture.md`** with the request-provided history flow, the message limit, and the no-persistence boundary.

Out of scope: a database, persistent or cross-session memory, RAG, tools, MCP, routing, LangGraph, a new endpoint, a new UI.

## Completion checks

1. Format and lint (`python -m uv run ruff format` and `python -m uv run ruff check`).
2. In a new Open WebUI chat, ask a prepared first question, for example "What is an API?".
3. Then ask a question that depends on it, for example "Give me a simple real-life example of that."
4. In the development log, confirm the role order is system, user, assistant, user.

**Expected result:** the second answer clearly builds on the first. Starting a new chat gives no memory of the old one. Do not add an evaluation harness, broad test suite or production memory features.

## Handover

**Files changed:** `src/learning_companion/chain.py` (message placeholder), the chat adapter in `src/learning_companion/main.py` (history conversion, limit, role log), `docs/architecture.md`. Commands run are the lint and start commands above.

**Story 3.1 extends:** the same conversation messages, adding a second, study-helper behaviour next to general chat.
