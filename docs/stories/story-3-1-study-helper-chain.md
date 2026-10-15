# Story 3.1 — Study-helper LangChain chain

## Purpose

Add a second behaviour to the same Learning Companion Chatbot: a study helper that explains beginner technical ideas in plain language. This story creates the capability only. Choosing between general chat and the study helper is Story 3.2.

## What this story implements in plain English

- The chatbot gains a second way of answering: a short, plain-language explanation of a beginner technical idea, with a small example where useful.
- Every study answer ends with one small suggested next step to learn.
- Ordinary chat in Open WebUI does not change. Greetings and general questions are answered exactly as before.
- The study helper is not yet reachable from Open WebUI. Developers can try it locally. This is a second set of instructions for the same model, not an autonomous agent.

## Prerequisites

- Stories 1.1–2.2 are complete and general chat with history works through Open WebUI.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1–2.2, the existing code, `.env.example`, and the chat adapter.
- Preserve the endpoints, Grok settings, request/response behaviour, Open WebUI connection and conversation-message handling.

## Work to do

1. **Leave the general-chat chain untouched.**
2. **Add one separately named study-helper chain**: prompt → Grok model → text output, using the same configured Grok model and the same message-history handling.
3. **Write the study-helper instruction** (kept separate from user content) so that it asks for:
   - a concise plain-language explanation;
   - a small example where useful;
   - one suggested next learning step.

   It must not claim to research, browse, retrieve course data, or guarantee correctness.
4. **Add a small project-local way to invoke the study-helper chain during development**, for example a short script or function. Do not change the existing endpoint's general-chat behaviour. Story 3.2 adds the visible `/study` rule.
5. **Update `docs/architecture.md`** with the two chain behaviours and their responsibilities, and state that selection between them is the next story.

Out of scope: routing, LLM-based classification, more specialists, loops, review steps, a second application, endpoint, provider or UI, a database, retrieval, MCP, tool calls, LangGraph.

## Completion checks

1. Format and lint (`python -m uv run ruff format` and `python -m uv run ruff check`).
2. Send one ordinary general-chat message in Open WebUI and confirm it behaves as before.
3. Run one focused local invocation of the study-helper chain, for example "Explain what an API is".

**Expected result:** the general reply is unchanged, and the study-helper reply has a plain explanation and one next step. Do not add broad tests or production controls.

## Handover

**Files changed:** the chains module (new study-helper prompt and chain), a small development invocation helper, `docs/architecture.md`. The commands run are the lint command and the local invocation.

**Story 3.2 extends:** the same chat endpoint with a visible Python rule that sends `/study` messages to this chain and everything else to general chat.
