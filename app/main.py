import asyncio
import secrets
from pathlib import Path
from uuid import uuid4
import httpx
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .corpus import DOCUMENTS, SAMPLE_REPORTS
from .knowledge import retrieve
from .schemas import Report, TicketIn, Approval, Resolution, KnowledgeIn, Query, Receipt
from .store import Store, Conflict, Missing
from .security import webhook_envelope

STATIC = Path(__file__).parent / "static"


def create_app(settings=None):
    cfg = settings or Settings()
    store = Store(cfg.db_path)
    for doc in DOCUMENTS:
        store.add_document(doc)
    if cfg.seed_demo and not store.list_tickets():
        for index, (text, location, requester, category, priority) in enumerate(SAMPLE_REPORTS):
            citation = next(d for d in DOCUMENTS if d["category"] == category)
            store.create({"request_id": f"sample-{index}", "text": text, "location": location, "requester": requester,
                "channel": "portal", "mode": "demo", "mode_used": "sample", "category": category, "priority": priority,
                "summary": text, "response": f"We have recorded your request. {citation['steps'][0]} [{citation['id']}]",
                "steps": citation["steps"], "citations": [{k: citation[k] for k in ("id", "title", "category", "trusted", "synthetic")} | {"excerpt": citation["content"], "score": 0}],
                "flags": [], "grounded": True, "automation_allowed": True, "execution_id": "",
                "trace": [{"name": "Sample fixture", "kind": "sample", "detail": "Seeded example for exploring the interface. Submit a new request to execute n8n."}]})

    app = FastAPI(title="RelayDesk data and retrieval service", version="1.0.0")
    app.state.store, app.state.settings = store, cfg

    @app.middleware("http")
    async def local_boundaries(request: Request, call_next):
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            origin = request.headers.get("origin")
            if origin and origin != f"{request.url.scheme}://{request.headers.get('host')}":
                return JSONResponse({"detail": "Cross-origin writes are not allowed"}, status_code=403)
        if request.url.path.startswith("/api/") and request.url.path != "/api/health" and cfg.portal_key:
            supplied = request.headers.get("X-Portal-Key", "")
            if not secrets.compare_digest(supplied, cfg.portal_key):
                return JSONResponse({"detail": "Portal key required"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.exception_handler(Conflict)
    async def conflict(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.exception_handler(Missing)
    async def missing(_, exc):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    def internal(x_relay_key: str = Header(default="")):
        if not cfg.internal_key or not secrets.compare_digest(x_relay_key, cfg.internal_key):
            raise HTTPException(401, "Internal authentication required")

    async def n8n(path, body):
        if not cfg.internal_key:
            raise HTTPException(503, "n8n authentication is not configured. Run the setup script.")
        payload, headers = webhook_envelope(body, cfg.internal_key)
        try:
            async with httpx.AsyncClient(timeout=cfg.request_timeout) as client:
                r = await client.post(cfg.n8n_url + "/webhook/" + path, json=payload, headers=headers)
                r.raise_for_status()
                result = r.json()
                if not isinstance(result, dict) or not result:
                    raise ValueError("Empty workflow response")
                return result
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, "n8n workflow unavailable or failed. Check workflow activation and execution history; retry with the same request ID.")

    @app.get("/api/health")
    async def health():
        async def check(url):
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    r = await client.get(url)
                    return r.status_code == 200
            except httpx.HTTPError:
                return False
        n8n_up, ollama_up = await asyncio.gather(check(cfg.n8n_url + "/healthz"), check(cfg.ollama_url + "/api/tags"))
        return {"status": "ok", "n8n": n8n_up, "ollama": ollama_up, "model": cfg.ollama_model, "editor_url": cfg.editor_url, "retrieval": "LangChain BM25 · lexical", "portal_key_required": bool(cfg.portal_key)}

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/api/tickets")
    def tickets():
        return {"tickets": store.list_tickets()}

    @app.get("/api/tickets/{ticket_id}")
    def ticket(ticket_id: str):
        return store.get(ticket_id)

    @app.post("/api/reports")
    async def report(body: Report):
        return await n8n("relaydesk-intake", body.model_dump())

    @app.post("/internal/email-report", dependencies=[Depends(internal)])
    async def email_report(body: Report):
        return await n8n("relaydesk-intake", {**body.model_dump(), "channel": "email"})

    @app.post("/internal/tickets", dependencies=[Depends(internal)])
    def save_ticket(body: TicketIn):
        return store.create(body.model_dump())

    @app.post("/api/tickets/{ticket_id}/approve")
    def approve(ticket_id: str, body: Approval):
        return store.approve(ticket_id, body.version, body.response)

    @app.post("/api/tickets/{ticket_id}/resolve")
    def resolve(ticket_id: str, body: Resolution):
        return store.resolve(ticket_id, body.version, body.note)

    @app.get("/api/knowledge")
    def knowledge():
        return {"documents": store.documents()}

    @app.post("/api/knowledge")
    def add_knowledge(body: KnowledgeIn):
        return store.add_document({"id": "KB-CUSTOM-" + uuid4().hex[:8].upper(), **body.model_dump(), "synthetic": False, "steps": []})

    @app.post("/api/knowledge/search")
    @app.post("/internal/retrieve", dependencies=[Depends(internal)])
    def search(body: Query):
        return {"citations": retrieve(store.documents(), body.query, body.category), "retrieval": "BM25 lexical retrieval via LangChain"}

    @app.get("/api/outbox")
    def outbox():
        return {"events": store.outbox(), "pending_count": store.pending_count()}

    @app.get("/internal/handoff/pending", dependencies=[Depends(internal)])
    def pending():
        return {"events": store.outbox(pending_only=True)}

    @app.post("/internal/handoff/receipt", dependencies=[Depends(internal)])
    def receipt(body: Receipt):
        return store.handoff(body.event_id, body.execution_id)

    @app.post("/api/automations/run")
    async def run_handoff():
        return await n8n("relaydesk-handoff", {})

    @app.get("/api/export")
    def export():
        return {"project": "RelayDesk", "tickets": [store.get(t["id"]) for t in store.list_tickets()], "outbox": store.outbox(limit=None), "knowledge": store.documents()}

    @app.get("/")
    def root():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
