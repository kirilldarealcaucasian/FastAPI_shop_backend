"""ASGI entrypoint for `uvicorn cmd:app`."""

from application.cmd import app

__all__ = ("app",)
