"""ASGI entrypoint for `uvicorn auth.main:app`."""

from auth.cmd import app

__all__ = ("app",)
