"""A small LangGraph that reuses the existing chains, with one bounded review.

START -> router -> (general_chat | study_helper) -> reviewer
reviewer -> END                                  (approved)
reviewer -> improver -> reviewer                 (improve, only while revision_count is 0)

State lives for one request only; nothing is stored afterwards.
"""

from typing import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph

from .chain import (
    Review,
    build_chain,
    build_improve_chain,
    build_review_chain,
    build_study_chain,
)
from .config import Settings
from .routing import choose_route

MAX_REVISIONS = 1


class GraphState(TypedDict):
    user_message: str  # the latest thing the user asked (marker removed by the router)
    messages: list[BaseMessage]  # recent conversation of this request (Story 2.2)
    route: str  # "general" or "study", chosen by the router
    draft_answer: str  # written by a helper (or the improver), not yet final
    review_decision: str  # "approve" or "improve"
    review_reason: str  # one short sentence explaining the decision
    revision_count: int  # improvements so far (0 or 1)
    final_answer: str  # the reply sent to the user


NODE_FOR_ROUTE = {"general": "general_chat", "study": "study_helper"}


def build_graph(settings: Settings):
    """Compile the graph. Raises ConfigurationError if the model settings are missing."""
    general_chain = build_chain(settings)
    study_chain = build_study_chain(settings)
    review_chain = build_review_chain(settings)
    improve_chain = build_improve_chain(settings)

    def router(state: GraphState) -> dict:
        # Ordinary Python, not an agent: the Story 3.2 /study rule.
        route, message = choose_route(state["user_message"])
        return {"route": route, "user_message": message}

    def general_chat(state: GraphState) -> dict:
        draft = general_chain.invoke(
            {"history": state["messages"], "question": state["user_message"]}
        )
        return {"draft_answer": draft}

    def study_helper(state: GraphState) -> dict:
        if not state["user_message"]:
            return {"draft_answer": "Add a question after /study."}
        draft = study_chain.invoke(
            {"history": state["messages"], "question": state["user_message"]}
        )
        return {"draft_answer": draft}

    def reviewer(state: GraphState) -> dict:
        if not state["user_message"]:
            review = Review(decision="approve", reason="No question to review.")
        else:
            try:
                review = review_chain.invoke(
                    {
                        "route": state["route"],
                        "question": state["user_message"],
                        "draft": state["draft_answer"],
                    }
                )
            except Exception as exc:  # noqa: BLE001 - a failed review must not lose the answer
                review = Review(
                    decision="approve",
                    reason=f"Review unavailable ({type(exc).__name__}).",
                )
        decision = review.decision
        if state["revision_count"] >= MAX_REVISIONS:
            decision = "approve"  # the bound: after one improvement, always finish
        output = {"review_decision": decision, "review_reason": review.reason}
        if decision == "approve":
            output["final_answer"] = state["draft_answer"]
        return output

    def improver(state: GraphState) -> dict:
        improved = improve_chain.invoke(
            {
                "route": state["route"],
                "question": state["user_message"],
                "reason": state["review_reason"],
                "draft": state["draft_answer"],
            }
        )
        return {
            "draft_answer": improved,
            "revision_count": state["revision_count"] + 1,
        }

    def after_review(state: GraphState) -> str:
        wants_improvement = state["review_decision"] == "improve"
        if wants_improvement and state["revision_count"] < MAX_REVISIONS:
            return "improver"
        return END

    graph = StateGraph(GraphState)
    graph.add_node("router", router)
    graph.add_node("general_chat", general_chat)
    graph.add_node("study_helper", study_helper)
    graph.add_node("reviewer", reviewer)
    graph.add_node("improver", improver)
    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", lambda s: NODE_FOR_ROUTE[s["route"]])
    graph.add_edge("general_chat", "reviewer")
    graph.add_edge("study_helper", "reviewer")
    graph.add_conditional_edges("reviewer", after_review, ["improver", END])
    graph.add_edge("improver", "reviewer")
    return graph.compile()


def run_graph_events(graph, user_message: str, messages: list[BaseMessage]):
    """Run one request, reporting progress as it happens.

    Yields ("route", route) as soon as the router has chosen, then
    ("done", route, final_answer, trace) when the graph has finished.
    """
    state: GraphState = {
        "user_message": user_message,
        "messages": messages,
        "route": "",
        "draft_answer": "",
        "review_decision": "",
        "review_reason": "",
        "revision_count": 0,
        "final_answer": "",
    }
    nodes: list[str] = []
    decisions: list[str] = []
    for update in graph.stream(state, stream_mode="updates"):
        for name, output in update.items():
            nodes.append(name)
            state.update(output)
            if name == "router":
                yield ("route", state["route"])
            if name == "reviewer":
                decisions.append(output["review_decision"])
    trace = (
        f"route={state['route']} | review={' then '.join(decisions)} | "
        f"revisions={state['revision_count']} | " + " → ".join(["START", *nodes, "END"])
    )
    yield ("done", state["route"], state["final_answer"], trace)


def run_graph(graph, user_message: str, messages: list[BaseMessage]):
    """Run one request. Returns (route, final_answer, trace)."""
    *_, (_, route, final_answer, trace) = run_graph_events(
        graph, user_message, messages
    )
    return route, final_answer, trace
