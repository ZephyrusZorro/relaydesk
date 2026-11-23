# RelayDesk 2.0 — redesign and orchestration upgrade

**Goal:** Connect the website visibly to the running n8n instance, replace the interface with a premium operations console, and improve reliability and retrieval efficiency without discarding existing data.

**Design:** White and cool-gray work surfaces, ink typography, cobalt controls, compact navigation, a real workload overview, readable request rows and a dedicated workflow operations view. Processing moves to a durable background queue with visible n8n-reported stages. Existing evidence inspection, approvals, speech and exports remain available.

**Architecture:** Browser → durable jobs API → independent Docker worker → authenticated n8n specialist workflow → cached hybrid lexical retrieval → persistent ticket → human approval → n8n handoff. A dedicated authenticated n8n connection-check workflow provides an actual website-to-n8n handshake. SQLite lease tokens prevent stale workers from finishing reclaimed jobs. Exponential retry is bounded. Retrieval caches a versioned BM25/character-similarity index, invalidates on knowledge changes and exposes measured diagnostics. No semantic embeddings or production-scale claims are introduced.

**Alternatives considered:** A cosmetic reskin would not improve execution. Redis/Postgres/queue-mode n8n would increase deployment and migration costs for this small local application. The chosen modular worker adds meaningful concurrency, recovery and observability while preserving the existing volume and n8n ownership of the agent workflow.

**Constraints:** No Telegram. No invented n8n owner credentials. Preserve current tickets, documents, keys and approval history. Keep ports local and retain short-lived JWT ingress. Workflow status must distinguish a live handshake, configured templates and actual execution. Agent and source output remains untrusted until validated and reviewed.

## Stages

- [x] 1. Tests first: durable jobs, lease reclamation, idempotency, retry bounds, retrieval cache/invalidation and API contracts. Implement storage and retrieval modules.
- [x] 2. Implement worker, connection probe and progress callbacks; regenerate/import/publish the n8n workflows. Verify the real website → worker → n8n → ticket path and preserve existing data.
- [x] 3. Rebuild the interface, asynchronous composer, workflow monitor, current job list, job timeline inspector, knowledge review governance and retrieval diagnostics. Check desktop/mobile, request/review/handoff and unavailable-state behavior.
- [x] 4. Independent review, contrast/layout/select/sidebar polish, regression fixes, benchmark cached retrieval, run the suites and actual LLM integration, update the handover and package the new release.

## Review focus

Concurrent claims must not duplicate ownership. Expired leases must reject stale completion and stop retry loops. Enqueue must redact before persistence and reject conflicting request IDs. Knowledge additions must invalidate both index and query caches. n8n callbacks must not regress a terminal job. The UI must never infer successful execution from a static diagram or a green container health check alone.
