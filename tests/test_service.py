import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings

KEY = "test-internal-key-long-enough-12345"
HEAD = {"X-Relay-Key": KEY}


@pytest.fixture
def client(tmp_path):
    settings = Settings(db_path=str(tmp_path / "relay.db"), internal_key=KEY, seed_demo=False, n8n_url="http://127.0.0.1:9")
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


def test_cross_origin_write_rejected(client):
    assert client.post("/api/knowledge/search", headers={"Origin": "https://other.example"}, json={"query": "VPN"}).status_code == 403


def test_optional_portal_key_protects_records(tmp_path):
    cfg = Settings(db_path=str(tmp_path / "key.db"), internal_key=KEY, portal_key="portal-test-key", seed_demo=False)
    with TestClient(create_app(cfg)) as c:
        assert c.get("/api/tickets").status_code == 401
        assert c.get("/api/export").status_code == 401
        assert c.get("/api/tickets", headers={"X-Portal-Key": "portal-test-key"}).status_code == 200


def test_portal_and_assets_are_served(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200


def test_retrieval_accepts_full_length_report(client):
    query = "VPN tunnel disconnects. " + "Detail about the issue. " * 140
    assert 2000 < len(query) < 4000
    result = client.post("/internal/retrieve", headers=HEAD, json={"query": query, "category": "vpn"})
    assert result.status_code == 200
    assert result.json()["citations"][0]["id"] == "KB-VPN-01"


def test_category_filter_precedes_top_k():
    from app.knowledge import retrieve
    documents = [{"id": f"wrong-{i}", "title": "VPN tunnel connection", "category": "network", "content": "VPN tunnel connection repeatedly drops. " * 3, "trusted": True} for i in range(4)]
    documents += [{"id": "expected-vpn", "title": "Remote access", "category": "vpn", "content": "Record the tunnel failure and contact the service desk.", "trusted": True}]
    documents += [{"id": f"background-{i}", "title": "Printer supplies", "category": "device", "content": "Monitor the ink cartridge stock and paper inventory.", "trusted": True} for i in range(10)]
    found = retrieve(documents, "VPN tunnel connection", "vpn")
    assert found and found[0]["id"] == "expected-vpn"


def test_outbox_pagination_does_not_hide_pending_or_export_history(client):
    store = client.app.state.store
    for i in range(101):
        t = store.create(ticket_payload(request_id=f"bulk-request-{i}"))
        store.approve(t["id"], 1, "Reviewed VPN draft.")
    all_events = client.get("/api/export").json()["outbox"]
    assert len(all_events) == 101
    oldest_id = sorted(all_events, key=lambda event: event["created_at"])[0]["id"]
    pending = client.get("/internal/handoff/pending", headers=HEAD).json()["events"]
    assert pending[0]["id"] == oldest_id
    for event in pending:
        store.handoff(event["id"], "test-batch")
    assert client.get("/api/outbox").json()["pending_count"] == 1
    assert len(client.get("/api/export").json()["outbox"]) == 101


def test_receipt_counts_only_new_transition(client):
    t = save(client)
    client.post(f"/api/tickets/{t['id']}/approve", json={"version": 1, "response": "Reviewed response"})
    event = client.get("/api/outbox").json()["events"][0]
    body = {"event_id": event["id"], "execution_id": "concurrent-check"}
    assert client.post("/internal/handoff/receipt", headers=HEAD, json=body).json()["newly_delivered"] is True
    assert client.post("/internal/handoff/receipt", headers=HEAD, json=body).json()["newly_delivered"] is False


def test_webhook_boundary_redacts_before_n8n_and_uses_expiring_token():
    import json
    import jwt
    from app.security import webhook_envelope
    payload, headers = webhook_envelope({"text": "VPN broke. My password is ExampleSecretForTest."}, KEY)
    assert "ExampleSecretForTest" not in json.dumps(payload)
    assert payload["input_redacted"] is True
    assert "X-Relay-Key" not in headers
    assert KEY not in json.dumps(headers)
    claims = jwt.decode(headers["Authorization"].split()[1], KEY, algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 30


def test_ingress_redacts_punctuation_and_metadata_without_expanding_input():
    import json
    from app.security import webhook_envelope
    text = "a" * 3992 + " token=x"
    assert len(text) == 4000
    payload, _ = webhook_envelope({"text": text, "location": "token=mock.suffix42", "requester": 'password="two secret words"'}, KEY)
    assert len(payload["text"]) == 4000
    assert "mock.suffix42" not in json.dumps(payload)
    assert "two secret words" not in json.dumps(payload)
