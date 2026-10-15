# Story 3.2 — Visible Python routing between the two chains

## Purpose

Make both chains reachable from the same Open WebUI chat through one simple, visible Python rule. Participants see an ordinary `if/else` that Story 4.1 will later replace with an explicit LangGraph route.

## What this story implements in plain English

- A normal message in Open WebUI is answered by general chat, as before.
- A message starting with `/study`, for example `/study Explain what an API is`, is answered by the study helper.
- The answer or the development log shows which path was used, `general` or `study`, so participants can see why.
- This is a fixed rule written in plain Python. It is not smart routing and not an autonomous agent.

## Prerequisites

- Stories 1.1–3.1 are complete: general-chat and study-helper chains both exist.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1–3.1, the existing code, both chains, `.env.example`, and the chat adapter.
- Preserve the Open WebUI connection, endpoints, Grok settings, message-history handling and the normal JSON/SSE response shapes.

## Work to do

1. **Add one visible Python rule** in a small, clearly named function: if the latest user message begins with `/study`, select the study-helper chain; otherwise select the general-chat chain.
2. **Strip only the leading `/study` marker** before passing the current question to the study helper. Keep all other request messages as history under the Story 2.2 rules.
3. **Record the route** (`general` or `study`) in a compact development log or safe development-only trace. When practical without breaking the OpenAI-compatible shape, add a short route label to the answer text. Create no custom response fields and no Open WebUI plugins.
4. **Use the existing normal and streaming adapter** for both chains, so both routes work from the same Open WebUI conversation.
5. **Update `docs/architecture.md`** with the `/study` rule, the selected-chain path, and the boundary: deterministic application routing, not LLM classification, LangGraph or multi-agent orchestration.

Out of scope: LLM routing, extra specialists, review steps, loops, broad tests, production controls.

## Completion checks

1. Format and lint (`python -m uv run ruff format` and `python -m uv run ruff check`).
2. In Open WebUI, send a general message such as "Hello".
3. Send `/study Explain what an API is`.
4. Check the route log or trace shows `general`, then `study`.

**Expected result:** both replies arrive through the same endpoint. The study reply has a clear explanation and one next step, and the `/study` marker is not echoed back as part of the question.

## Handover

**Files changed:** the routing function and the chat adapter in `src/learning_companion/`, `docs/architecture.md`. The commands run are the lint and start commands above.

**Story 4.1 extends:** the same chains inside a small LangGraph, with explicit state, a router node, conditional edges, a reviewer and one improvement step.
