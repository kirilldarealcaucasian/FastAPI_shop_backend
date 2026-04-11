"""ASGI entrypoint for `uvicorn events_collector.main:app`."""

from .cmd import app

__all__ = ("app",)
