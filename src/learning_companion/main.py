import json
import logging
import re
import time
import uuid
from typing import Literal

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from .chain import ConfigurationError, prompt_roles, to_history
from .config import get_settings
from .graph import build_graph, run_graph, run_graph_events

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Learning Companion Chatbot")


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str | list | None = None


def _text(content: str | list | None) -> str:
    """Plain text of a message; non-text parts (images etc.) are ignored."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            p.get("text", "")
            for p in content
            if isinstance(p, dict) and p.get("type") == "text"
        )
    return ""


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message]
    stream: bool = False


def _error(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"message": message}})


def _pieces(text: str) -> list[str]:
    """Split text into word-sized pieces (each keeps its trailing whitespace)."""
    return re.findall(r"\S+\s*|\s+", text)


def _sse(data: dict | str) -> str:
    return f"data: {data if isinstance(data, str) else json.dumps(data)}\n\n"


def _chunk(
    completion_id: str, created: int, model: str, delta: dict, finish: str | None
) -> dict:
    return {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/v1/models")
def list_models() -> dict:
    name = get_settings().grok_model_name or "learning-companion"
    return {
        "object": "list",
        "data": [
            {
                "id": name,
                "object": "model",
                "created": 0,
                "owned_by": "learning-companion",
            }
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(request: ChatRequest):
    settings = get_settings()

    # Story 2.2: the latest user message is the question; earlier user/assistant
    # messages from this request become history. Nothing is stored between requests.
    last_user = next(
        (
            i
            for i in range(len(request.messages) - 1, -1, -1)
            if request.messages[i].role == "user"
        ),
        None,
    )
    question = (
        _text(request.messages[last_user].content) if last_user is not None else ""
    )
    if not question:
        return _error(400, "No user message found.")

    history = to_history(
        [(m.role, _text(m.content)) for m in request.messages[:last_user]]
    )

    try:
        graph = build_graph(settings)
    except ConfigurationError as exc:
        return _error(503, str(exc))

    # Development view: roles only. A request "system" message never reaches the prompt.
    ignored = [m.role for m in request.messages if m.role == "system"]
    logger.info(
        "prompt roles=%s | request messages=%d | history used=%d | ignored request system messages=%d",
        prompt_roles(history, question),
        len(request.messages),
        len(history),
        len(ignored),
    )

    model_name = request.model or settings.grok_model_name
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    created = int(time.time())

    def answer_text() -> str:
        route, answer, trace = run_graph(graph, question, history)
        logger.info(trace)
        return f"[route: {route}]\n\n{answer}"

    if not request.stream:
        try:
            answer = answer_text()
        except Exception as exc:  # noqa: BLE001 - surface provider errors honestly
            return _error(502, f"Model call failed: {exc}")
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": answer},
                    "finish_reason": "stop",
                }
            ],
        }

    def events():
        def content(text: str) -> str:
            return _sse(
                _chunk(completion_id, created, model_name, {"content": text}, None)
            )

        yield _sse(
            _chunk(completion_id, created, model_name, {"role": "assistant"}, None)
        )
        streamed = False
        try:
            for event in run_graph_events(graph, question, history):
                kind = event[0]
                if kind == "route":
                    # The router has chosen: show the label at once.
                    yield content(f"[route: {event[1]}]\n\n")
                elif kind == "token":
                    # Model text goes out as it is written.
                    streamed = True
                    yield content(event[1])
                elif kind == "improve":
                    # The draft is already on screen; the improved answer follows it.
                    yield content("\n\n---\n**Improved answer:**\n\n")
                else:
                    _, _, answer, trace = event
                    logger.info(trace)
                    if not streamed:  # e.g. "/study" with no question: no model text
                        for piece in _pieces(answer):
                            yield content(piece)
        except Exception as exc:  # noqa: BLE001
            yield content(f"[Model call failed: {exc}]")
        yield _sse(_chunk(completion_id, created, model_name, {}, "stop"))
        yield _sse("[DONE]")

    return StreamingResponse(events(), media_type="text/event-stream")


def run() -> None:
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port)
