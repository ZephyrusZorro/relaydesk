import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor
from app.store import Store, Conflict
from app.jobs import JobQueue
from app.retrieval import KnowledgeIndex
from app.corpus import DOCUMENTS


@pytest.fixture
def queue(tmp_path):
    return JobQueue(Store(str(tmp_path / "jobs.db")))


def report(i=1):
    return {"request_id": f"durable-request-{i}", "text": "VPN tunnel disconnects repeatedly", "location": "Office", "requester": "Operator", "mode": "demo", "channel": "portal"}


def test_enqueue_is_redacted_and_idempotent(queue):
    body = report() | {"text": "VPN fails. password=mock.suffix42"}
    first = queue.enqueue(body)
    assert queue.enqueue(body)["id"] == first["id"]
    assert "mock.suffix42" not in str(queue.get(first["id"], private=True))
    with pytest.raises(Conflict):
        queue.enqueue(report())


def test_concurrent_claim_has_one_owner(queue):
    queue.enqueue(report(), epoch=100)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda i: queue.claim(f"worker-{i}", epoch=100, lease=30), range(2)))
    assert sum(c is not None for c in claims) == 1


def test_expired_lease_reclaims_and_rejects_old_completion(queue):
    job = queue.enqueue(report(), epoch=100)
    first = queue.claim("worker-a", epoch=100, lease=30)
    second = queue.claim("worker-b", epoch=131, lease=30)
    assert second["attempts"] == 2
    assert any("lease expired" in ev["detail"].lower() for ev in queue.get(job["id"])["events"])
    assert not queue.finish(job["id"], first["run_token"], ticket_id="stale", epoch=132)
    assert queue.finish(job["id"], second["run_token"], ticket_id="current", epoch=132)
    assert queue.get(job["id"])["ticket_id"] == "current"


def test_retry_backoff_is_bounded_and_manual_retry_preserves_identity(queue):
    job = queue.enqueue(report(), epoch=100)
    for i in range(3):
        claim = queue.claim("worker", epoch=100 + i * 100)
        queue.fail(job["id"], claim["run_token"], "n8n unavailable", epoch=101 + i * 100)
    assert queue.get(job["id"])["state"] == "failed"
    assert queue.claim("worker", epoch=1000) is None
    retried = queue.retry(job["id"], epoch=1000)
    assert retried["id"] == job["id"] and retried["attempts"] == 3
    assert queue.claim("worker", epoch=1000)["attempts"] == 4


def test_terminal_job_ignores_late_progress(queue):
    job = queue.enqueue(report(), epoch=100)
    run = queue.claim("worker", epoch=100)
    queue.finish(job["id"], run["run_token"], ticket_id="ticket", epoch=101)
    queue.progress(report()["request_id"], "drafting", "123")
    assert queue.get(job["id"])["stage"] == "completed"


def test_hybrid_index_reuses_work_and_invalidates_on_addition(tmp_path):
    store = Store(str(tmp_path / "retrieval.db"))
    for doc in DOCUMENTS:
        store.add_document(doc)
    index = KnowledgeIndex(store)
    first = index.search("VPN tunnel disconnects", "vpn")
    second = index.search("VPN tunnel disconnects", "vpn")
    assert first["citations"][0]["id"] == "KB-VPN-01"
    assert second["diagnostics"]["cache_hit"] is True
    assert index.stats()["builds"] == 1
    store.add_document({"id": "KB-ORION", "title": "Orion projector", "category": "device", "content": "Orion projector HDMI input and visible source cable procedure.", "trusted": False, "synthetic": True})
    added = index.search("Orion projector HDMI", "device")
    assert added["citations"][0]["id"] == "KB-ORION"
    assert index.stats()["builds"] == 2


def test_async_api_queues_without_blocking_on_n8n(tmp_path):
    from fastapi.testclient import TestClient
    from app.config import Settings
    from app.main import create_app
    with TestClient(create_app(Settings(db_path=str(tmp_path / "api.db"), seed_demo=False, internal_key="x"*64, n8n_url="http://127.0.0.1:9"))) as client:
        response = client.post("/api/jobs", json=report())
        assert response.status_code == 202
        job = response.json()
        assert job["state"] == "queued" and "run_token" not in job
        assert client.post("/api/jobs", json=report()).json()["id"] == job["id"]
        assert client.get("/api/jobs/"+job["id"]).json()["events"][0]["stage"] == "queued"


def test_worker_dispatch_persists_completion_and_network_failure_retries(queue):
    import httpx
    from app.config import Settings
    from app.worker import execute
    stored = queue.store.create(report() | {"mode_used": "demo"})
    queued = queue.enqueue(report())
    claim = queue.claim("worker")
    settings = Settings(internal_key="x"*64)
    async def success():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"id": stored["id"]}))) as client:
            await execute(queue, settings, claim, client)
    asyncio.run(success())
    assert queue.get(queued["id"])["ticket_id"] == stored["id"]
    failed = queue.enqueue(report(2))
    claim = queue.claim("worker")
    async def unavailable():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(503))) as client:
            await execute(queue, settings, claim, client)
    asyncio.run(unavailable())
    assert queue.get(failed["id"])["state"] == "retrying"
