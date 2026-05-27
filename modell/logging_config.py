from __future__ import annotations

import logging
from typing import Any


DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configure_logging(level: int | str = logging.INFO, *, force: bool = True, **kwargs: Any) -> None:
    if isinstance(level, str):
        numeric_level = logging.getLevelName(level.upper())
        if isinstance(numeric_level, str):
            numeric_level = logging.INFO
    else:
        numeric_level = level

    logging.basicConfig(
        level=numeric_level,
        format=kwargs.get("format", DEFAULT_LOG_FORMAT),
        force=force,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)