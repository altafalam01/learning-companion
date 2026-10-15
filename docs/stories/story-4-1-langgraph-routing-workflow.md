# Story 4.1 — LangGraph routing workflow

## Purpose

Replace only the internal `if/else` route from Story 3.2 with one small LangGraph workflow that reuses the existing chains. The user-facing behaviour stays the same. What changes is that the route, state, nodes and edges become visible in code.

## What this story implements in plain English

- A message enters the chatbot and is first looked at by a router, which is ordinary Python and not an AI.
- The router decides: a message starting with `/study` goes to the study helper, and anything else goes to general chat.
- The chosen helper writes the answer, and that answer goes back to Open WebUI as before.
- Nothing looks different in Open WebUI. Only the development log is more informative, showing the route and the steps taken.

## Prerequisites

- Stories 1.1–3.2 are complete and both routes work in Open WebUI.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1–3.2, the existing LangChain chains, `.env.example`, and the chat adapter.
- Preserve the Open WebUI connection, API endpoints, request/response shape, Grok configuration, normal JSON replies and streaming SSE behaviour.

## Work to do

1. **Explain the state first.** Before any implementation, write in plain English what each state field means:
   - `user_message`: the latest thing the user asked;
   - `messages`: the recent conversation of this request, handled as in Story 2.2;
   - `route`: `general` or `study`, chosen by the router;
   - `final_answer`: the finished reply.

   The state lives for one request only.
2. **Add `langgraph` as a dependency** (`python -m uv add langgraph`).
3. **Create `src/learning_companion/graph.py`** with a minimal typed graph state holding those four fields.
4. **Add exactly three nodes.** A node is a focused piece of work, not automatically an agent.
   - **Router:** ordinary Python logic, not an agent. It reuses the existing `/study` rule and writes `general` or `study` into state.
   - **General-chat node:** calls the existing general-chat chain and writes the final answer.
   - **Study-helper node:** calls the existing study-helper chain and writes the final answer. The two answer nodes may be described as small specialist behaviours.
5. **Add explicit edges:** `START → router`; conditional edges from the router to the general-chat or study-helper node; and an edge from each answer node to `END`. No reviewer, improver, loop or retry. Story 4.2 adds the bounded review path.
6. **Hand the request to the graph from `main.py`** instead of choosing a chain with `if/else`. Keep the FastAPI service, the OpenAI-compatible endpoint, the Grok settings and the history conversion. Create no second app or chat route.
7. **Keep the existing normal and streaming adapter.** The graph's final answer flows through it so Open WebUI shows the result as before. No custom response format.
8. **Add a compact, safe development trace** reporting the route and node sequence, for example `route=study | graph: START → router → study_helper → END`. Never expose API keys or full hidden prompts.
9. **Update `docs/architecture.md`** with the graph diagram, state fields, node responsibilities, edge rules and what remains out of scope.

An MCP tool call could be placed inside a future node, but MCP is not implemented in this course story.

Out of scope: databases, persistence, RAG, web search, tool execution, MCP, human approval, review steps, loops, extra agents, broad tests, security programmes, observability platforms, deployment.

## Completion checks

1. Format and lint (`python -m uv run ruff format` and `python -m uv run ruff check`).
2. In Open WebUI, ask a general question such as "Hello".
3. Ask `/study Explain what an API is`.
4. Inspect the trace.

**Expected result:**
- General: the reply reaches Open WebUI, and the trace shows `route=general | graph: START → router → general_chat → END`.
- Study: the reply reaches Open WebUI with an explanation and one next step, and the trace shows `route=study | graph: START → router → study_helper → END`.

## Handover

**Files changed:** `pyproject.toml`, `uv.lock`, `src/learning_companion/graph.py` (new), `src/learning_companion/main.py`, `docs/architecture.md`. The commands run are the dependency add, lint and start commands above.

**Story 4.2 extends:** the same graph with a reviewer and an improver, allowing at most one improvement before the graph ends.
