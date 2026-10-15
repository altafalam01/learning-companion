"""Development helper: try the study-helper chain without Open WebUI.

Run: python -m learning_companion.dev_study "Explain what an API is"
"""

import sys

from .chain import ConfigurationError, build_study_chain
from .config import get_settings


def main() -> None:
    question = " ".join(sys.argv[1:]).strip() or "Explain what an API is"
    try:
        chain = build_study_chain(get_settings())
    except ConfigurationError as exc:
        sys.exit(str(exc))
    print(chain.invoke({"history": [], "question": question}))


if __name__ == "__main__":
    main()
