import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class Conflict(Exception):
    pass


class Missing(Exception):
    pass


class Store:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, input_hash TEXT NOT NULL,
                    status TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, ticket_id TEXT NOT NULL, action TEXT NOT NULL,
                    detail TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbox (
                    id TEXT PRIMARY KEY, ticket_id TEXT UNIQUE NOT NULL, status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0, execution_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL, delivered_at TEXT);
                CREATE TABLE IF NOT EXISTS knowledge (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def add_document(self, document):
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO knowledge VALUES (?,?)", (document["id"], json.dumps(document)))
        return document

    def documents(self):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute("SELECT payload FROM knowledge ORDER BY id")]

    def _unpack(self, row):
        return {**json.loads(row["payload"]), **{k: row[k] for k in ("id", "status", "version", "created_at", "updated_at")}}

    def list_tickets(self):
        with self.connect() as db:
            return [self._unpack(row) for row in db.execute("SELECT * FROM tickets ORDER BY created_at DESC")]

    def get(self, ticket_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
            if row is None:
                raise Missing("Ticket not found")
            ticket = self._unpack(row)
            ticket["audit"] = [dict(a) for a in db.execute("SELECT action,detail,created_at FROM audit WHERE ticket_id=? ORDER BY id", (ticket_id,))]
            return ticket

    def create(self, payload):
        signature = json.dumps({k: payload[k] for k in ("text", "location", "requester", "channel", "mode")}, sort_keys=True)
        fingerprint = hashlib.sha256(signature.encode()).hexdigest()
        ticket_id, timestamp = "RD-" + uuid4().hex[:8].upper(), now()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            prior = db.execute("SELECT * FROM tickets WHERE request_id=?", (payload["request_id"],)).fetchone()
            if prior:
                if prior["input_hash"] != fingerprint:
                    raise Conflict("This request ID was already used for different input")
                ticket_id = prior["id"]
            else:
                db.execute("INSERT INTO tickets VALUES (?,?,?,'needs_review',1,?,?,?)", (ticket_id, payload["request_id"], fingerprint, json.dumps(payload), timestamp, timestamp))
                db.execute("INSERT INTO audit(ticket_id,action,detail,created_at) VALUES (?,?,?,?)", (ticket_id, "created", f"Created through {payload['channel']}; mode: {payload['mode_used']}", timestamp))
        return self.get(ticket_id)

    def approve(self, ticket_id, version, response):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
            if not row:
                raise Missing("Ticket not found")
            if row["version"] != version or row["status"] != "needs_review":
                raise Conflict("Ticket changed. Reload before approving")
            payload = json.loads(row["payload"])
            if not payload["automation_allowed"] or not payload["grounded"] or not payload["citations"]:
                raise Conflict("This draft is blocked. Add reliable context and submit a new request")
            payload["approved_response"] = response
            timestamp = now()
            db.execute("UPDATE tickets SET status='approved',version=version+1,payload=?,updated_at=? WHERE id=?", (json.dumps(payload), timestamp, ticket_id))
            db.execute("INSERT INTO outbox(id,ticket_id,status,created_at) VALUES (?,?,'pending',?)", ("EV-" + uuid4().hex[:12], ticket_id, timestamp))
            db.execute("INSERT INTO audit(ticket_id,action,detail,created_at) VALUES (?,?,?,?)", (ticket_id, "approved", "Operator reviewed and approved the response; handoff queued", timestamp))
        return self.get(ticket_id)

    def resolve(self, ticket_id, version, note):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
            if not row:
                raise Missing("Ticket not found")
            if row["version"] != version or row["status"] != "approved":
                raise Conflict("Only a current, approved ticket can be resolved")
            db.execute("UPDATE tickets SET status='resolved',version=version+1,updated_at=? WHERE id=?", (now(), ticket_id))
            db.execute("INSERT INTO audit(ticket_id,action,detail,created_at) VALUES (?,?,?,?)", (ticket_id, "resolved", note, now()))
        return self.get(ticket_id)

    def outbox(self, pending_only=False):
        with self.connect() as db:
            query = "SELECT * FROM outbox" + (" WHERE status='pending'" if pending_only else "") + " ORDER BY created_at DESC LIMIT 100"
            return [dict(r) for r in db.execute(query)]

    def handoff(self, event_id, execution_id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM outbox WHERE id=?", (event_id,)).fetchone()
            if not row:
                raise Missing("Handoff event not found")
            if row["status"] != "delivered":
                timestamp = now()
                db.execute("UPDATE outbox SET status='delivered', attempts=attempts+1,execution_id=?,delivered_at=? WHERE id=?", (execution_id, timestamp, event_id))
                db.execute("INSERT INTO audit(ticket_id,action,detail,created_at) VALUES (?,?,?,?)", (row["ticket_id"], "handoff_delivered", "n8n recorded an internal support handoff; no external message sent", timestamp))
        return {"event_id": event_id, "status": "delivered"}
