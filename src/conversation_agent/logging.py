"""Readable checkpoint logging for the live demo."""

import json
import logging
import sys
from typing import Any

# Keep demo checkpoints readable on stdout without duplicate root-logger output.
demo_logger = logging.getLogger("DEMO")
demo_logger.setLevel(logging.INFO)
demo_logger.propagate = False
demo_logger.handlers.clear()
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
demo_logger.addHandler(handler)


def log_demo(label: str, value: Any) -> None:
    """Print one readable block for the live demo."""

    if not isinstance(value, str):
        value = json.dumps(
            value,
            indent=2,
            default=lambda item: (
                item.model_dump(mode="json") if hasattr(item, "model_dump") else str(item)
            ),
        )

    line = "─" * 60
    demo_logger.info("\n%s\nDEMO · %s\n%s\n%s", line, label, value, line)
