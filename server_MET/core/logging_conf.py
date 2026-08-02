"""Configuração centralizada de logging do projeto."""
from __future__ import annotations

import logging

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(level=level, format=_FORMAT)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


__all__ = ["setup_logging", "get_logger"]
