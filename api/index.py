"""Vercel serverless function entrypoint."""

from __future__ import annotations

from typing import Any
from app.main import app as _fastapi_app


async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    """ASGI wrapper that restores original request path on Vercel rewrites."""
    if scope["type"] == "http":
        headers = dict(scope.get("headers", []))
        # Vercel passes the original incoming URL in x-matched-path
        matched_path = headers.get(b"x-matched-path")
        if matched_path:
            decoded = matched_path.decode("utf-8")
            scope["path"] = decoded.split("?")[0]

    await _fastapi_app(scope, receive, send)
