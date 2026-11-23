import asyncio
import hashlib
import json
import time
from pathlib import Path
import httpx
from .transport import invoke_n8n
from .store import now


class Operations:
    def __init__(self, settings, queue, index):
        self.settings, self.queue, self.index = settings, queue, index
        self.last = None
        self.expiry = 0
        self.lock = asyncio.Lock()

    async def snapshot(self, force=False):
        async with self.lock:
            if not force and self.last and time.monotonic() < self.expiry:
                return {**self.last, "jobs": self.queue.metrics(), "retrieval_stats": self.index.stats()}
            async def probe():
                try:
                    async with httpx.AsyncClient(timeout=4) as client:
                        result = await invoke_n8n(self.settings, "relaydesk-status", {}, client)
                        return result.get("status") == "connected", result
                except (httpx.HTTPError, ValueError, RuntimeError):
                    return False, {}
            async def model():
                try:
                    async with httpx.AsyncClient(timeout=2) as client:
                        response = await client.get(self.settings.ollama_url + "/api/tags")
                        response.raise_for_status()
                        names = [item["name"] for item in response.json().get("models", [])]
                        return True, self.settings.ollama_model in names
                except (httpx.HTTPError, ValueError, KeyError):
                    return False, False
            (connected, handshake), (ollama, ready) = await asyncio.gather(probe(), model())
            flows = []
            directory = Path(__file__).resolve().parents[1] / "workflows"
            if directory.exists():
                for file in sorted(directory.glob("*.json")):
                    raw = file.read_bytes()
                    flow = json.loads(raw)
                    flows.append({"id": flow["id"], "name": flow["name"], "revision": hashlib.sha256(raw).hexdigest()[:10], "nodes": len(flow["nodes"]), "agents": sum(n["type"].endswith(".agent") for n in flow["nodes"]), "optional": "Email" in flow["id"], "editor_url": self.settings.editor_url + "/workflow/" + flow["id"]})
            self.last = {"status": "ok", "n8n": connected, "handshake": handshake, "verified_at": now(), "ollama": ollama, "model_ready": ready, "model": self.settings.ollama_model, "editor_url": self.settings.editor_url, "retrieval": "Hybrid lexical · cached BM25 + character similarity", "portal_key_required": bool(self.settings.portal_key), "workflows": flows, "jobs": self.queue.metrics(), "retrieval_stats": self.index.stats(), "version": "2.0.0"}
            self.expiry = time.monotonic() + 5
            return self.last
