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
from .retrieval import KnowledgeIndex
from .jobs import JobQueue
from .operations import Operations
from .transport import invoke_n8n
from .schemas import Report, TicketIn, Approval, Resolution, KnowledgeIn, KnowledgeTrust, Query, Receipt
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

    queue = JobQueue(store)
    index = KnowledgeIndex(store)
    operations = Operations(cfg, queue, index)
    app = FastAPI(title="RelayDesk operations service", version="2.0.0")
    app.state.store, app.state.settings = store, cfg
    app.state.queue = queue
    app.state.index = index

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
        try:
            return await invoke_n8n(cfg, path, body)
        except (httpx.HTTPError, ValueError, RuntimeError):
            raise HTTPException(503, "n8n workflow unavailable or failed. Check workflow activation and execution history; retry with the same request ID.")

    @app.get("/api/health")
    async def health():
        return await operations.snapshot()

    @app.post("/api/integrations/check")
    async def check_integrations():
        return await operations.snapshot(force=True)

    @app.post("/api/jobs", status_code=202)
    def enqueue_report(body: Report):
        return queue.enqueue(body.model_dump())

    @app.get("/api/jobs")
    def jobs():
        return {"jobs": queue.list(), "metrics": queue.metrics()}

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        return queue.get(job_id)

    @app.post("/api/jobs/{job_id}/retry")
    def retry_job(job_id: str):
        return queue.retry(job_id)

    @app.post("/internal/jobs/progress", dependencies=[Depends(internal)])
    def progress(body: dict):
        queue.progress(str(body.get("request_id", "")), str(body.get("stage", "")), str(body.get("execution_id", "")), body.get("run_token"))
        return body.get("context", {})

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

    @app.patch("/api/knowledge/{doc_id}")
    def update_knowledge_trust(doc_id: str, body: KnowledgeTrust):
        return store.set_document_trust(doc_id, body.trusted)

    @app.delete("/api/knowledge/{doc_id}")
    def remove_knowledge(doc_id: str):
        return store.delete_document(doc_id)

    @app.post("/api/knowledge/search")
    @app.post("/internal/retrieve", dependencies=[Depends(internal)])
    def search(body: Query):
        return index.search(body.query, body.category)

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
