"""Bounded durable dispatcher. n8n runs every specialist agent."""
import asyncio
import os
import socket
import sys
import httpx
from .config import Settings
from .store import Store, Missing
from .jobs import JobQueue
from .transport import invoke_n8n


async def execute(queue, settings, job, client=None):
    try:
        result = await invoke_n8n(settings, "relaydesk-intake", {**job["payload"], "job_token": job["run_token"]}, client)
        ticket_id = result.get("id")
        if not isinstance(ticket_id, str):
            raise ValueError("n8n did not return a ticket")
        queue.store.get(ticket_id)
        queue.finish(job["id"], job["run_token"], ticket_id)
    except (httpx.HTTPError, ValueError, RuntimeError, Missing):
        queue.fail(job["id"], job["run_token"], "n8n execution unavailable or invalid; automatic retry is bounded")


async def serve():
    settings = Settings()
    queue = JobQueue(Store(settings.db_path))
    worker_id = socket.gethostname() + ":" + str(os.getpid())
    if "--health" in sys.argv:
        return 0 if queue.metrics()["worker_online"] else 1

    async def pulse():
        while True:
            queue.heartbeat(worker_id)
            await asyncio.sleep(5)

    heartbeat = asyncio.create_task(pulse())
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            while True:
                job = queue.claim(worker_id, lease=max(settings.request_timeout+45, 300))
                if job:
                    await execute(queue, settings, job, client)
                    print(f"RelayDesk worker: {job['id']} processed", flush=True)
                else:
                    await asyncio.sleep(1)
    finally:
        heartbeat.cancel()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(serve()))
    except KeyboardInterrupt:
        pass
