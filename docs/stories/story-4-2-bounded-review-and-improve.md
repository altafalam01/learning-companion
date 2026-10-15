# Story 4.2 — Bounded answer review and improvement

## Purpose

Extend the existing three-node graph so the chatbot checks a draft answer once, improves it once only when needed, and then stops. This does not rebuild the graph. It adds a reviewer and an improver and shows a visible, bounded cycle.

## What this story implements in plain English

- After a helper writes a draft, a reviewer reads it and says "approve" or "improve", with one short reason.
- If the draft is approved, it is sent to Open WebUI as the final answer.
- If it needs work, an improver rewrites it once, and the reviewer checks it one last time.
- After one improvement the chatbot always stops. It never keeps correcting itself, and it does no research and uses no tools.

## Prerequisites

- Stories 1.1–4.1 are complete: the LangGraph router and two answer nodes work in Open WebUI.
- Read first: `docs/config.yaml` (if present), `docs/architecture.md`, Stories 1.1–4.1, the existing graph state and nodes, both answer chains, `.env.example`, and the chat adapter.
- Preserve the Open WebUI connection, endpoints, request/response shape, Grok configuration, normal JSON replies, streaming SSE behaviour and the routing path.

## Work to do

1. **Explain the new state first.** Before implementation, describe each new field in plain English:
   - `draft_answer`: the answer written by a helper, not yet checked;
   - `review_decision`: `approve` or `improve`;
   - `review_reason`: one short sentence explaining the decision;
   - `revision_count`: how many improvements have happened (0 or 1);
   - `final_answer`: the reply sent to the user.

   Extend the typed state only with these fields.
2. **Change the answer nodes** only as needed so they write `draft_answer` instead of `final_answer`.
3. **Add the answer-reviewer node** (Grok-powered). It receives the draft and the selected route. Against a short fixed classroom rule, it decides whether the draft is clear and appropriate for the general-chat or study-helper role. It returns a structured `approve` or `improve` decision and one short reason.
4. **Add the answer-improver node** (Grok-powered). It receives the draft and the reviewer's reason, rewrites the answer once, and increments `revision_count`. It uses no tools, does not browse or retrieve, makes no plan and makes no routing choice.
5. **Add the bounded edges:**
   - each answer node → reviewer;
   - approve → `END`, with the draft becoming `final_answer`;
   - improve → improver, only when `revision_count` is 0;
   - improver → reviewer, for one final check.

   When `revision_count` is 1, the reviewer must accept the current draft as final and end. This is the only cycle: reviewer → improver → reviewer, at most once. No other loop, retry, planner, tool or open-ended agent behaviour.
6. **Keep the existing adapter.** The graph's final answer goes through the existing normal and streaming OpenAI-compatible adapter. Add no custom Open WebUI events.
7. **Add a compact, safe development trace** with the route, reviewer decision, revision count and node sequence. Never expose API keys or full hidden prompts.
8. **Update `docs/architecture.md`** with the two new nodes, state additions, the full graph diagram, edge rules, the one-revision limit and the scope boundary.

Terminology: the reviewer and improver are small LLM-powered specialist nodes, which may be called specialist agents in this classroom example. The router remains ordinary Python, not an agent. There is no MCP tool call. An MCP call could be a future node, but it is outside this story.

Out of scope: databases, persistence, RAG, web search, tools, MCP, human approval, additional agents, broad tests, production controls, observability platforms, deployment.

## Completion checks

1. Format and lint (`python -m uv run ruff format` and `python -m uv run ruff check`).
2. In Open WebUI, ask an ordinary question the reviewer approves directly.
3. Ask a `/study` question chosen to benefit from clearer wording, and watch the review → improve → review path.
4. Confirm the final answer shows in Open WebUI, and inspect the trace.

**Expected result:**
- Ordinary question: the trace shows `route=general | review=approve | revisions=0 | START → router → general_chat → reviewer → END`.
- Study question: the trace shows `route=study | review=improve then approve | revisions=1 | START → router → study_helper → reviewer → improver → reviewer → END`. The improved final answer is shown in Open WebUI.

## Handover

**Files changed:** `src/learning_companion/graph.py` (state fields, reviewer and improver nodes, bounded edges), the chat adapter in `src/learning_companion/main.py` if the trace needs it, `docs/architecture.md`. The commands run are the lint and start commands above.

**Final capstone outcome:** a Learning Companion Chatbot in Open WebUI. LangChain composes the model work, and a small LangGraph controls the route: a router chooses a specialist, a reviewer checks the draft, an improver revises at most once, and the graph then ends. A participant can explain every node, edge and state field.
