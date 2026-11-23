"""Durable dispatch queue. Agent decisions remain in n8n."""
import hashlib
import json
import time
from uuid import uuid4
from .store import Conflict, Missing, now
from .security import sanitize_fields


class JobQueue:
    def __init__(self, store):
        self.store = store
        with store.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, fingerprint TEXT NOT NULL,
                  payload TEXT NOT NULL, state TEXT NOT NULL, stage TEXT NOT NULL,
                  attempts INTEGER NOT NULL DEFAULT 0, max_attempts INTEGER NOT NULL DEFAULT 3,
                  run_token TEXT, worker_id TEXT, lease_until REAL, next_attempt REAL NOT NULL,
                  ticket_id TEXT, error TEXT, execution_id TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS jobs_ready ON jobs(state,next_attempt);
                CREATE TABLE IF NOT EXISTS job_events (
                  id INTEGER PRIMARY KEY,job_id TEXT NOT NULL,stage TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workers (id TEXT PRIMARY KEY, heartbeat REAL NOT NULL);
            """)

    def _public(self, row):
        if not row:
            raise Missing("Processing job not found")
        value = dict(row)
        payload = json.loads(value.pop("payload"))
        for field in ("run_token", "fingerprint", "worker_id", "lease_until", "next_attempt"):
            value.pop(field, None)
        value.update(requester=payload.get("requester", "Operator"), summary=payload["text"][:120], mode=payload["mode"])
        return value

    def enqueue(self, body, epoch=None):
        epoch = time.time() if epoch is None else epoch
        payload = sanitize_fields(body)
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        ident = "JOB-" + uuid4().hex[:12].upper()
        stamp = now()
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT * FROM jobs WHERE request_id=?", (payload["request_id"],)).fetchone()
            if previous:
                if previous["fingerprint"] != digest:
                    raise Conflict("This request ID already belongs to different input")
                return self._public(previous)
            db.execute("INSERT INTO jobs(id,request_id,fingerprint,payload,state,stage,next_attempt,created_at,updated_at) VALUES (?,?,?,?,'queued','queued',?,?,?)", (ident, payload["request_id"], digest, encoded, epoch, stamp, stamp))
            db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,'queued','Request safely queued for n8n',?)", (ident, stamp))
        return self.get(ident)

    def get(self, ident, private=False):
        with self.store.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (ident,)).fetchone()
            if not row:
                raise Missing("Processing job not found")
            result = dict(row) if private else self._public(row)
            if private:
                result["payload"] = json.loads(result["payload"])
            result["events"] = [dict(r) for r in db.execute("SELECT stage,detail,created_at FROM job_events WHERE job_id=? ORDER BY id", (ident,))]
            return result

    def list(self):
        with self.store.connect() as db:
            return [self._public(r) for r in db.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 40")]

    def claim(self, worker_id, epoch=None, lease=300):
        epoch = time.time() if epoch is None else epoch
        token = uuid4().hex
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            expired = db.execute("SELECT id,attempts,max_attempts FROM jobs WHERE state='running' AND lease_until<=?", (epoch,)).fetchall()
            if expired:
                ts = now()
                db.execute("UPDATE jobs SET state=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'queued' END,stage=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'queued' END,error='Previous worker lease expired',next_attempt=?,run_token=NULL,updated_at=? WHERE state='running' AND lease_until<=?", (epoch, ts, epoch))
                for item in expired:
                    next_stage = "failed" if item["attempts"] >= item["max_attempts"] else "queued"
                    detail = "Worker lease expired after max attempts" if next_stage == "failed" else "Worker lease expired; job requeued for another attempt"
                    db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,?,?,?)", (item["id"], next_stage, detail, ts))
            row = db.execute("SELECT id FROM jobs WHERE state IN ('queued','retrying') AND next_attempt<=? AND attempts<max_attempts ORDER BY created_at,id LIMIT 1", (epoch,)).fetchone()
            if not row:
                return None
            ident = row["id"]
            db.execute("UPDATE jobs SET state='running',stage='dispatching',attempts=attempts+1,run_token=?,worker_id=?,lease_until=?,updated_at=? WHERE id=?", (token, worker_id, epoch+lease, now(), ident))
            db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,'dispatching','Worker dispatching to authenticated n8n webhook',?)", (ident, now()))
        return self.get(ident, private=True)

    def finish(self, ident, token, ticket_id, epoch=None):
        epoch = time.time() if epoch is None else epoch
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            result = db.execute("UPDATE jobs SET state='completed',stage='completed',ticket_id=?,error=NULL,run_token=NULL,updated_at=? WHERE id=? AND state='running' AND run_token=? AND lease_until>?", (ticket_id, now(), ident, token, epoch))
            if result.rowcount:
                db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,'completed','n8n persisted a review ticket',?)", (ident, now()))
            return bool(result.rowcount)

    def fail(self, ident, token, message, epoch=None):
        epoch = time.time() if epoch is None else epoch
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM jobs WHERE id=? AND state='running' AND run_token=? AND lease_until>?", (ident, token, epoch)).fetchone()
            if not row:
                return False
            state = "failed" if row["attempts"] >= row["max_attempts"] else "retrying"
            delay = min(60, 2 ** row["attempts"])
            db.execute("UPDATE jobs SET state=?,stage=?,error=?,next_attempt=?,run_token=NULL,updated_at=? WHERE id=?", (state, state, message[:240], epoch+delay, now(), ident))
            db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,?,?,?)", (ident, state, message[:240], now()))
            return True

    def retry(self, ident, epoch=None):
        with self.store.connect() as db:
            result = db.execute("UPDATE jobs SET state='queued',stage='queued',max_attempts=attempts+3,error=NULL,next_attempt=?,updated_at=? WHERE id=? AND state='failed'", (time.time() if epoch is None else epoch, now(), ident))
            if not result.rowcount:
                raise Conflict("Only failed jobs can be retried")
            db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,'queued','Operator requested another bounded retry cycle',?)", (ident, now()))
        return self.get(ident)

    def progress(self, request_id, stage, execution_id, run_token=None):
        allowed = {"classifying", "retrieving", "drafting", "reviewing", "persisting"}
        if stage not in allowed:
            raise Conflict("Unknown workflow stage")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id,stage FROM jobs WHERE request_id=? AND state='running' AND run_token=? AND lease_until>?", (request_id, run_token, time.time())).fetchone()
            ranks = {s: i for i,s in enumerate(["dispatching", "classifying", "retrieving", "drafting", "reviewing", "persisting"])}
            if row and ranks.get(row["stage"], -1)>ranks[stage]:
                return False
            if row and row["stage"] != stage:
                db.execute("UPDATE jobs SET stage=?,execution_id=?,updated_at=? WHERE id=?", (stage, execution_id, now(), row["id"]))
                db.execute("INSERT INTO job_events(job_id,stage,detail,created_at) VALUES (?,?,?,?)", (row["id"], stage, "Stage reported by n8n execution " + execution_id, now()))
        return bool(row)

    def heartbeat(self, worker_id):
        with self.store.connect() as db:
            db.execute("INSERT INTO workers VALUES (?,?) ON CONFLICT(id) DO UPDATE SET heartbeat=excluded.heartbeat", (worker_id, time.time()))

    def metrics(self):
        with self.store.connect() as db:
            counts = {r[0]: r[1] for r in db.execute("SELECT state,COUNT(*) FROM jobs GROUP BY state")}
            last = db.execute("SELECT MAX(heartbeat) FROM workers").fetchone()[0]
        return {"counts": counts, "worker_online": bool(last and time.time()-last<20), "worker_last_seen": last}
