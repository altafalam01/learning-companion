# Architecture — Learning Companion Chatbot

## Purpose

A small **Learning Companion Chatbot** for a beginner LangChain and LangGraph classroom course. It is one application that grows session by session. It is not a custom frontend and not a second demo application.

## Classroom flow

```
Open WebUI → this local application's OpenAI-compatible chat endpoint → LangChain prompt and Grok model → answer in Open WebUI
```

| Part | Role |
|---|---|
| Open WebUI | Already installed and working. It is the supplied chat client only. Participants do not reinstall, reconfigure, modify, or build it. |
| Chat endpoint | FastAPI app with `GET /health`, `GET /v1/models`, and `POST /v1/chat/completions` (JSON, or text-only SSE when `stream` is true). |
| Prompt and messages | A fixed Learning Companion system instruction, kept separate from the user's message. |
| LangChain model | Prompt → Grok chat model → text output, configured from environment settings. |
| Provider API | Grok API at `GROK_API_BASE_URL`. |

## Message flow (Story 2.1)

For each chat request the app builds a two-part LangChain chat prompt, in this order:

1. `system`: the application-owned Learning Companion instruction (a fixed `SystemMessage`, never templated).
2. earlier `human` / `ai` messages from the same request (Story 2.2, a message placeholder).
3. `human`: the latest `user` message from the request.

A `system` message supplied in the request is user-provided content and never replaces the application instruction; it is not added to the prompt. A development log line shows the prompt roles, the request message count and the number of ignored request system messages. It never logs keys, the hidden instruction or message text.

**No persistence:** the app saves nothing after a request completes.

## Conversation history (Story 2.2)

Open WebUI sends the messages of the active chat with every request. The app converts the earlier `user` and `assistant` messages (before the latest user message) into LangChain messages, in their original order, and places them between the system instruction and the latest question.

- **Limit:** only the last `MAX_HISTORY_MESSAGES` (6) earlier messages are used.
- Request `system` messages and non-text parts are ignored safely.
- **No persistence:** nothing is saved after the request. A new chat starts fresh.
- The log also shows how many history messages were used.

## Two chain behaviours (Story 3.1)

Both chains are prompt → the same configured Grok model → text output, and both use the same request history handling.

| Chain | Responsibility |
|---|---|
| General chat (`build_chain`) | Greetings and ordinary conversation. Unchanged. |
| Study helper (`build_study_chain`) | A concise plain-language explanation of a beginner technical idea, a small example where useful, and one next learning step. It does not research, browse, retrieve course data or guarantee correctness. |

Each chain has its own fixed instruction, kept separate from user content. `python -m learning_companion.dev_study "Explain what an API is"` tries the study helper without Open WebUI.

## LangGraph workflow with one bounded review (Stories 4.1 and 4.2)

The routing `if/else` is a small LangGraph in `graph.py`. The two chains above are reused as they are. Story 4.2 adds a reviewer and an improver, with a limit of one improvement.

```
START → router → general_chat → reviewer → END
                → study_helper → reviewer → END
                                   reviewer → improver → reviewer → END   (at most once)
```

**State** (one request only, nothing stored afterwards):

| Field | Meaning |
|---|---|
| `user_message` | The latest thing the user asked. The router removes a leading `/study`. |
| `messages` | Recent conversation of this request, handled as in Story 2.2. |
| `route` | `general` or `study`, chosen by the router. |
| `draft_answer` | The answer written by a helper (or rewritten by the improver), not yet final. |
| `review_decision` | `approve` or `improve`. |
| `review_reason` | One short sentence explaining the decision. |
| `revision_count` | How many improvements have happened (0 or 1). |
| `final_answer` | The reply sent to the user. |

**Nodes:**
- `router`: ordinary Python, not an agent. It applies the `/study` rule from `routing.choose_route`.
- `general_chat` and `study_helper`: call the existing chains and write `draft_answer`.
- `reviewer`: a small Grok-powered specialist. It reads the draft and the route against a short fixed rule (general: friendly, clear, brief; study: concise explanation, small example where useful, one final `Next step:` line) and returns a structured `approve` or `improve` plus one reason. On approval the draft becomes `final_answer`.
- `improver`: a small Grok-powered specialist. It rewrites the draft once using the reviewer's reason and increments `revision_count`. It uses no tools, does not browse or retrieve, makes no plan and makes no routing choice.

**Edges:** `START → router`; router to `general_chat` or `study_helper` by `route`; each answer node to `reviewer`; `reviewer → END` when approved; `reviewer → improver` only when the decision is `improve` and `revision_count` is 0; `improver → reviewer` for one final check. When `revision_count` is 1 the reviewer always accepts the current draft and the graph ends. This is the only cycle (reviewer, improver, reviewer, at most once). There is no other loop, retry, planner or tool.

If the reviewer call itself fails, the draft is approved as it is and the reason says the review was unavailable, so a review problem never loses an answer.

`main.py` hands the request to the graph. The final answer goes through the same OpenAI-compatible adapter, starting with a `[route: ...]` label. Streaming requests send the `[route: ...]` label as soon as the router has chosen, then the reviewed answer in small word-sized chunks, then the stop chunk and `[DONE]`. The answer is released only after review (it may still be improved), so the text appears gradually after the graph finishes, not while the model is writing the draft. The development log shows a trace such as `route=study | review=improve then approve | revisions=1 | START → router → study_helper → reviewer → improver → reviewer → END`. It never shows keys, hidden prompts or answer text.

Out of scope: LLM routing, more than one improvement, tools, MCP, retrieval, web search, human approval, databases, persistence.

## Direct Python call vs. this LangChain flow

A direct call means we write the provider client, the system and user messages, the request, and the response extraction ourselves. As the chatbot grows (history, streaming, new roles, a different model), that glue code repeats.

LangChain organises these parts: prompt construction, message formats, the provider chat model, and output parsing. For a single fixed call, plain Python would still be enough.

## Boundaries

- API keys live only in an untracked `.env`. `.env.example` has blank values.
- Application instructions stay separate from user messages.
- The app starts without a real key. It returns a configuration error only when a model call is attempted.
- Out of scope: authentication, authorization, security hardening, databases, persistent memory, RAG, production deployment, and extensive tests.

## Configuration

`APP_ENV`, `GROK_API_KEY`, `GROK_API_BASE_URL`, `GROK_MODEL_NAME`, `HOST`, `PORT`. The instructor supplies the model name.

## Capstone outcome

A Learning Companion Chatbot in Open WebUI. LangChain composes the model work. A small LangGraph controls the route: a router chooses a specialist, a reviewer checks the draft, an improver revises at most once, and the graph then ends.
