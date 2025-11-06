"""Supabase client helpers."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

from django.conf import settings

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - handled at runtime (siko sure!)
    Client = Any  # type: ignore
    create_client = None  # type: ignore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Return a cached Supabase client instance."""

    if not settings.SUPABASE_URL or not (settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY):
        raise RuntimeError("Supabase credentials are not configured. Please set SUPABASE_URL and SUPABASE_KEY.")

    if create_client is None:  # pragma: no cover - safety guard if dependency missing
        raise RuntimeError("supabase package is not installed. Add 'supabase' to your dependencies.")

    api_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_KEY

    return create_client(settings.SUPABASE_URL, api_key)


def extract_response_error(response: Any) -> Optional[str]:
    """Normalize error from various Supabase response shapes."""

    if response is None:
        return None

    error: Optional[str] = None

    if hasattr(response, "error") and response.error:
        error = getattr(response.error, "message", None) or str(response.error)
    elif isinstance(response, dict):
        if response.get("error"):
            error_data = response["error"]
            if isinstance(error_data, dict):
                error = error_data.get("message") or error_data.get("error")
            else:
                error = str(error_data)

    return error


def extract_response_data(response: Any) -> Dict[str, Any]:
    """Return response data regardless of concrete return type."""

    if response is None:
        return {}

    if hasattr(response, "data"):
        return getattr(response, "data") or {}

    if isinstance(response, dict):
        return response.get("data") or {k: v for k, v in response.items() if k != "error"}

    return {}


def get_public_url(path: str) -> str:
    """Build a public URL for a stored object."""

    client = get_supabase_client()
    bucket = client.storage.from_(settings.SUPABASE_POST_IMAGE_BUCKET)
    response = bucket.get_public_url(path)

    if isinstance(response, str):
        return response

    data = extract_response_data(response)
    if isinstance(data, dict):
        return data.get("publicUrl") or data.get("publicURL") or data.get("public_url") or ""

    return ""

