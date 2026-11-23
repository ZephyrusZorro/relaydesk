"""Authenticated service-to-n8n transport shared by API and worker."""
import httpx
from .security import webhook_envelope


async def invoke_n8n(settings, path, body, client=None):
    if not settings.internal_key:
        raise RuntimeError("n8n authentication is not configured")
    payload, headers = webhook_envelope(body, settings.internal_key)
    owned = client is None
    session = client or httpx.AsyncClient(timeout=settings.request_timeout)
    try:
        response = await session.post(settings.n8n_url + "/webhook/" + path, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict) or not result:
            raise ValueError("Empty n8n workflow response")
        return result
    finally:
        if owned:
            await session.aclose()
