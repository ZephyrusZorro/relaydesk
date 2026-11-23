"""Minimize webhook input before n8n can retain trigger data."""
import re
import time
from uuid import uuid4
import jwt

SECRET_PATTERN = re.compile(r'''\b(password|passcode|recovery code|access token|token)\s*(?:is|=|:)\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\S+)''', re.I)


def webhook_envelope(body, key):
    payload = dict(body)
    for field in ("text", "location", "requester"):
        if field not in payload:
            continue
        original = payload[field]
        payload[field] = SECRET_PATTERN.sub(lambda match: match.group(0)[:-len(match.group(2))] + "*" * len(match.group(2)), original)
        if payload[field] != original:
            payload["input_redacted"] = True
    issued = int(time.time())
    token = jwt.encode({"sub": "relaydesk-service", "iat": issued, "exp": issued + 30, "jti": uuid4().hex}, key, algorithm="HS256")
    return payload, {"Authorization": "Bearer " + token}
