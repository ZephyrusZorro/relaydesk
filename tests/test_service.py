import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

KEY = "test-internal-key-long-enough-12345"
HEAD = {"X-Relay-Key": KEY}


@pytest.fixture
def client(tmp_path):
    settings = Settings(db_path=str(tmp_path / "relay.db"), internal_key=KEY, seed_demo=False)
    with TestClient(create_app(settings)) as c:
        yield c


def ticket_payload(**overrides):
    return {
        "request_id": "req-example-001", "text": "My VPN disconnects repeatedly",
        "location": "Remote office", "requester": "Alex", "channel": "portal",
        "mode": "demo", "mode_used": "demo", "category": "vpn", "priority": "normal",
        "summary": "VPN disconnects", "response": "Check network connectivity. [KB-VPN-01]",
        "steps": ["Check network connectivity"], "citations": [{"id": "KB-VPN-01", "title": "VPN connectivity", "excerpt": "Check connectivity", "category": "vpn", "trusted": True, "synthetic": True}],
        "flags": [], "grounded": True, "automation_allowed": True,
        "trace": [{"name": "Intake specialist", "detail": "Classified as VPN", "kind": "rule"}],
        "execution_id": "1", **overrides,
    }


def save(client, **overrides):
    r = client.post("/internal/tickets", headers=HEAD, json=ticket_payload(**overrides))
    assert r.status_code == 200, r.text
    return r.json()


def test_internal_endpoints_require_secret(client):
    assert client.post("/internal/retrieve", json={"query": "VPN"}).status_code == 401


def test_retrieval_returns_relevant_source_and_abstains(client):
    r = client.post("/internal/retrieve", headers=HEAD, json={"query": "VPN disconnects tunnel remote", "category": "vpn"})
    assert r.status_code == 200
    assert r.json()["citations"][0]["id"] == "KB-VPN-01"
    assert r.json()["citations"][0]["synthetic"] is True
    r = client.post("/api/knowledge/search", json={"query": "quantum entanglement cooking recipe"})
    assert r.json()["citations"] == []


def test_duplicate_ingestion_is_idempotent(client):
    first = save(client)
    second = save(client)
    assert first["id"] == second["id"]
    assert len(client.get("/api/tickets").json()["tickets"]) == 1
    conflict = client.post("/internal/tickets", headers=HEAD, json=ticket_payload(text="Different input under same request ID"))
    assert conflict.status_code == 409


def test_approval_is_version_checked_and_creates_one_outbox(client):
    t = save(client)
    r = client.post(f"/api/tickets/{t['id']}/approve", json={"version": 1, "response": "Operator reviewed the VPN draft."})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"
    assert len(client.get("/api/outbox").json()["events"]) == 1
    r = client.post(f"/api/tickets/{t['id']}/approve", json={"version": 1, "response": "Stale draft"})
    assert r.status_code == 409
    assert len(client.get("/api/outbox").json()["events"]) == 1


def test_blocked_draft_cannot_be_approved(client):
    t = save(client, automation_allowed=False, flags=["insufficient_evidence"], grounded=False, citations=[])
    assert client.post(f"/api/tickets/{t['id']}/approve", json={"version": 1, "response": "Try this"}).status_code == 409


def test_resolution_requires_approval(client):
    t = save(client)
    assert client.post(f"/api/tickets/{t['id']}/resolve", json={"version": 1, "note": "Done"}).status_code == 409


def test_receipts_are_authenticated_and_idempotent(client):
    t = save(client)
    client.post(f"/api/tickets/{t['id']}/approve", json={"version": 1, "response": "Reviewed response"})
    event = client.get("/api/outbox").json()["events"][0]
    body = {"event_id": event["id"], "execution_id": "execution-2"}
    assert client.post("/internal/handoff/receipt", json=body).status_code == 401
    assert client.post("/internal/handoff/receipt", headers=HEAD, json=body).status_code == 200
    assert client.post("/internal/handoff/receipt", headers=HEAD, json=body).status_code == 200
    assert client.get("/api/outbox").json()["events"][0]["status"] == "delivered"
    detail = client.get(f"/api/tickets/{t['id']}").json()
    assert sum(a["action"] == "handoff_delivered" for a in detail["audit"]) == 1


def test_knowledge_ingestion_is_searchable_and_untrusted_by_default(client):
    r = client.post("/api/knowledge", json={"title": "Projector setup", "category": "device", "content": "For the Orion projector, select HDMI input and check the source cable. Contact AV support for persistent failures."})
    assert r.status_code == 200
    found = client.post("/api/knowledge/search", json={"query": "Orion projector HDMI cable"}).json()["citations"]
    assert found[0]["title"] == "Projector setup"
    assert found[0]["trusted"] is False


def test_whitespace_and_oversized_input_rejected(client):
    assert client.post("/api/reports", json={"text": "   ", "location": "desk", "requester": "Alex"}).status_code == 422
    assert client.post("/api/reports", json={"text": "x" * 6000}).status_code == 422


def test_portal_does_not_pretend_to_work_without_n8n(client):
    r = client.post("/api/reports", json={"text": "VPN connection keeps dropping", "request_id": "no-n8n-request"})
    assert r.status_code == 503
    assert "n8n" in r.json()["detail"]


def test_state_persists_across_app_instances(tmp_path):
    cfg = Settings(db_path=str(tmp_path / "persist.db"), internal_key=KEY, seed_demo=False)
    with TestClient(create_app(cfg)) as c:
        t = save(c)
    with TestClient(create_app(cfg)) as c:
        assert c.get(f"/api/tickets/{t['id']}").status_code == 200
