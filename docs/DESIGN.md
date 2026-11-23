# RelayDesk design and decisions

The current user request supersedes the initial direction: do not base the project on a hackathon; implement mainly in n8n; use Docker; replace Telegram because it is unavailable to the user.

## Original project

RelayDesk is a voice-enabled internal IT support desk. Employees describe a Wi-Fi, VPN, account, software or device issue in a browser portal. Specialist n8n AI stages classify the request, retrieve approved troubleshooting procedures, draft an evidence-backed answer and review it. An operator edits and approves the response, then a separate n8n automation records a handoff. The portal doubles as a demonstrable support console, with persistent tickets, sources, execution traces and automation history.

This direction was chosen over a personal research assistant (weak operational automation) and an emergency assistant (hard to validate safely). It is an independently designed capstone, not an adaptation of a hackathon problem. No Telegram component is included. An optional email intake workflow is provided but requires mailbox configuration.

## n8n owns the workflow

The exported visual workflows own validation, classification branching, specialist LLM stages, evidence retrieval ordering, response review, deterministic guardrails, persistence calls and handoff routing. Native LangChain LLM Chain and Ollama Chat Model nodes implement three bounded specialist roles. These are a constrained multi-agent workflow, not unconstrained autonomous agents. A small Python service provides storage, BM25 retrieval through a LangChain retriever and the browser UI. It does not secretly duplicate the agent pipeline. If n8n is unavailable, new processing fails visibly.

The default demo mode uses clearly labeled deterministic stages and works without a downloaded model. Live mode uses a configured local Ollama model for classifier, resolver and reviewer. Missing/failed/invalid model responses fall back visibly to a constrained draft or abstention; they never authorize actions. Models cannot run shell commands, reset passwords or issue privileged actions.

## Persistence and integrity

SQLite stores tickets, knowledge, append-only application audit rows and an outbox. Request IDs prevent duplicate ingestion. Optimistic ticket versions reject stale approvals. Approval and outbox creation occur in the same transaction; only approved tickets can create a handoff. An n8n handoff workflow reads pending events and records idempotent receipts. Delivery is at-least-once; receipt deduplication prevents duplicate local handoff records. Edits remain operator responsibility. These audit records are not a tamper-proof or cryptographically immutable ledger.

Seeded procedures, employee names and service targets are fictional demo material. Citations expose stable chunk IDs and excerpts. New documents are untrusted until explicitly reviewed. Evidence absence, prompt-like input and invalid citations block automated handoff. Browser speech synthesis reads an answer and recognition optionally fills the report field. Speech availability depends on browser/OS support; typed input always works.

## Delivery

Docker Compose runs n8n and the data/portal service, with an optional Ollama profile. Ports bind to loopback. Windows and POSIX startup scripts generate local secrets, import versioned workflows and credentials, publish the core flows and launch the stack. No third-party messaging credentials are needed for the core demo. The n8n owner account is created by the user on first opening the editor; workflow setup should not require an account to be fabricated on their behalf.

Acceptance: submit, retrieve, inspect, edit/approve, hand off and resolve; no-evidence abstention; durable reload; stale and duplicate request handling; real n8n webhook execution; real local LLM check where available; desktop/mobile review; documented tests and remaining limits.
