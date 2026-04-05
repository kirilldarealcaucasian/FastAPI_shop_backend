"""ASGI entrypoint for `uvicorn events_collector.main:app`."""

from events_collector.cmd import app

__all__ = ("app",)
