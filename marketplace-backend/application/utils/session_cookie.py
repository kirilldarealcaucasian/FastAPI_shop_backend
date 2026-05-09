from datetime import datetime, timedelta

from fastapi import Response

from ..settings import settings


def prolong_events_session_cookie(response: Response, session_id: str) -> datetime:
    session_expiration_time = datetime.now() + timedelta(
        seconds=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS
    )
    response.set_cookie(
        key=settings.EVENTS_SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=settings.EVENTS_SESSION_EXPIRATION_COOKIE_NAME,
        value=session_expiration_time.isoformat(),
        max_age=settings.EVENTS_SESSION_COOKIE_MAX_AGE_SECONDS,
        httponly=False,
        secure=True,
        samesite="lax",
        path="/",
    )
    return session_expiration_time


__all__ = ("prolong_events_session_cookie",)
