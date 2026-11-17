"""Vercel serverless function entrypoint."""

from app.main import app

# ASGI application for Vercel Python runtime
app = app
