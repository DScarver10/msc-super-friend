from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    """
    Central logging configuration.
    Production evolution: structured JSON logs, request IDs, trace correlation.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
