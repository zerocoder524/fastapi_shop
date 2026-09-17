"""Compatibility shim. Endpoint implementations live in app/api/routes/."""

from .api.router import api_router

router = api_router
