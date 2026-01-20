"""Logging configuration for VideoTagger."""

import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """Configure logging for the application.

    Args:
        debug: If True, set level to DEBUG and show detailed output.
    """
    level = logging.DEBUG if debug else logging.INFO
    format_str = (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        if debug
        else "%(levelname)s: %(message)s"
    )

    logging.basicConfig(
        level=level,
        format=format_str,
        stream=sys.stderr,
        force=True,
    )

    # Reduce noise from third-party libraries
    if not debug:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
