"""The one visible routing rule. Story 4.1 replaces this if/else with a LangGraph route."""

STUDY_MARKER = "/study"


def choose_route(question: str) -> tuple[str, str]:
    """Return (route, question): "study" for a leading /study, else "general".

    Only the leading marker is removed; the rest of the question is untouched.
    """
    text = question.lstrip()
    if text.startswith(STUDY_MARKER) and (
        len(text) == len(STUDY_MARKER) or text[len(STUDY_MARKER)].isspace()
    ):
        return "study", text[len(STUDY_MARKER) :].strip()
    return "general", question
