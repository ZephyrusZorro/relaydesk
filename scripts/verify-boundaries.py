"""Additional real n8n edge checks; all data is synthetic and local."""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import httpx
import jwt
from dotenv import dotenv_values


def run():
    with httpx.Client(base_url="http://localhost:18080", timeout=250) as client:
        def submit(text, mode="demo"):
            response = client.post("/api/reports", json={"text": text, "location": "Boundary verification lab", "requester": "Boundary verification", "request_id": "boundary-" + uuid4().hex, "mode": mode})
            response.raise_for_status()
            return response.json()
        long_text = ("VPN tunnel disconnects. " + "Detailed context for the report boundary. " * 110)[:4000]
        assert len(long_text) == 4000
        long_ticket = submit(long_text)
        assert long_ticket["category"] == "vpn" and long_ticket["grounded"]
        hazard = submit("The office router is smoking and there is a burning smell.", "live")
        assert hazard["priority"] == "urgent" and not hazard["automation_allowed"]
        assert hazard["citations"] == [] and "Stop using" in hazard["response"]
        assert all("reconnect" not in step.lower() for step in hazard["steps"] if not step.startswith("Do not"))
        redacted = submit("VPN connection fails. My password is ExampleSecretForTest.")
        assert "ExampleSecretForTest" not in json.dumps(redacted)
        approval = client.post(f"/api/tickets/{redacted['id']}/approve", json={"version": 1, "response": redacted["response"]})
        approval.raise_for_status()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: client.post("/api/automations/run", json={}), range(2)))
        for result in results:
            result.raise_for_status()
        assert sum(result.json()["delivered"] for result in results) == 1
        assert client.post("/internal/handoff/receipt", json={"event_id": "forged-event"}).status_code == 401
        exact_text = ("VPN tunnel fails. " + "x" * 4000)[:3992] + " token=x"
        response = client.post("/api/reports", json={"text": exact_text, "location": "token=mock.suffix42", "requester": "Boundary verification", "request_id": "boundary-" + uuid4().hex, "mode": "demo"})
        response.raise_for_status()
        bounded = response.json()
        assert len(bounded["text"]) == 4000 and "mock.suffix42" not in json.dumps(bounded)
        config = dotenv_values(".env")
        expired = jwt.encode({"sub": "relaydesk-expiry-test", "exp": int(time.time()) - 60}, config["RELAYDESK_INTERNAL_KEY"], algorithm="HS256")
        rejected = httpx.post("http://localhost:" + config.get("RELAYDESK_N8N_PORT", "15678") + "/webhook/relaydesk-intake", json={}, headers={"Authorization": "Bearer " + expired}, timeout=10)
        assert rejected.status_code in {401, 403}
        return {"full_4000_character_report": True, "live_hazard_blocked": True, "secret_redacted_before_storage": True, "punctuated_metadata_redacted": True, "max_report_with_short_secret": True, "expired_jwt_rejected": True, "concurrent_handoff_count": sum(r.json()["delivered"] for r in results), "unauthenticated_receipt_rejected": True, "n8n_execution_ids": [long_ticket["execution_id"], hazard["execution_id"], redacted["execution_id"], bounded["execution_id"]]}


if __name__ == "__main__":
    result = run()
    Path("docs/boundary-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))
