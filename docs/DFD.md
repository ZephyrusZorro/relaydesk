# RelayDesk 2.0 — Data Flow Diagrams (DFD)

This document defines the **Level 0 (Context)**, **Level 1 (System Overview)**, and **Level 2 (Process Decomposition)** Data Flow Diagrams for **RelayDesk 2.0**, along with its data stores and trust boundaries.

---

## Level 0 DFD — Context Diagram

The context diagram shows all external entities interacting with the RelayDesk 2.0 system boundary.

```mermaid
flowchart LR
    Emp["Employee / Support Visitor"]
    Op["Support Operator"]
    LLM["Local Ollama LLM (llama3.2:3b)"]
    Mail["Optional IMAP Mailbox"]

    Sys(("0.0<br/>RelayDesk 2.0<br/>Support Operations System"))

    Emp -->|"Text or dictated IT issue<br/>(location, requester, mode)"| Sys
    Sys -->|"Live job stage updates,<br/>reviewed response & TTS audio"| Emp

    Op -->|"Draft edits, versioned approvals,<br/>resolution notes, custom procedures,<br/>review trust updates, handoff trigger"| Sys
    Sys -->|"Queue overview, evidence citations,<br/>agent trail, job timeline,<br/>handoff receipts & JSON export"| Op

    Sys -->|"Bounded JSON prompts +<br/>retrieved procedure excerpts"| LLM
    LLM -->|"Structured classification,<br/>sourced draft & review verdict"| Sys

    Mail -.->|"Optional inbound support emails<br/>(disabled by default)"| Sys
```

---

## Level 1 DFD — System Decomposition

The Level 1 DFD decomposes **RelayDesk 2.0** into seven core processes and four persistent SQLite data stores.

```mermaid
flowchart TB
    Emp["Employee / Support Visitor"]
    Op["Support Operator"]
    LLM["Local Ollama LLM"]
    Mail["Optional IMAP Mailbox"]

    P1(("1.0<br/>Intake Validation<br/>& Secret Redaction"))
    P2(("2.0<br/>Durable Job Queue<br/>& Leased Worker"))
    P3(("3.0<br/>n8n Multi-Agent<br/>Orchestration"))
    P4(("4.0<br/>Cached Hybrid<br/>Lexical RAG Engine"))
    P5(("5.0<br/>Human Review &<br/>Atomic Approval"))
    P6(("6.0<br/>Approved Handoff<br/>Execution"))
    P7(("7.0<br/>Knowledge<br/>Governance"))

    D1[("D1: Jobs &<br/>Job Events DB")]
    D2[("D2: Tickets &<br/>Audit Trail DB")]
    D3[("D3: Procedure Library<br/>& Revision DB")]
    D4[("D4: Durable<br/>Outbox DB")]

    Emp -->|"Support report<br/>(text / voice transcript)"| P1
    Mail -.->|"Optional email batch<br/>(03-email-optional)"| P1
    P1 -->|"Sanitized, redacted report<br/>(request_id + fingerprint)"| P2

    P2 <-->|"Enqueue, lease claim,<br/>heartbeat, retries & stage events"| D1
    P2 -->|"Signed 30s HS256 JWT +<br/>redacted payload + run_token"| P3
    P3 -->|"Live stage callbacks<br/>(X-Relay-Key)"| P2

    P3 -->|"Query + category"| P4
    P4 <-->|"Versioned snapshot &<br/>revision check"| D3
    P4 -->|"Top-3 ranked citations<br/>+ diagnostics"| P3

    P3 <-->|"Classifier, Resolution &<br/>Reviewer prompts / JSON"| LLM
    P3 -->|"Guarded needs_review ticket<br/>(citations, flags, trace)"| D2

    D2 -->|"Ticket drafts, evidence,<br/>agent trail & audit history"| P5
    D1 -->|"Job status & timeline"| P5
    Op -->|"Edited draft, approval,<br/>resolution note"| P5
    P5 -->|"Version-checked status<br/>& audit entries"| D2
    P5 -->|"Atomic pending handoff<br/>(BEGIN IMMEDIATE)"| D4

    Op -->|"Trigger handoffs"| P6
    D4 -->|"Pending outbox events"| P6
    P6 -->|"Idempotent receipt update"| D4
    P6 -->|"handoff_delivered audit"| D2

    Op -->|"Add, review/unreview,<br/>remove or search procedures"| P7
    P7 <-->|"CRUD + bump knowledge_revision"| D3
    P7 -->|"Playground query"| P4
    P4 -->|"Citations + cache hit/ms"| P7
```

---

## Level 2 DFD — Process 3.0 (n8n Multi-Agent Intake Pipeline)

This diagram details the internal data flows inside [`workflows/01-intake.json`](../workflows/01-intake.json), including the deterministic Demo path, the 3-agent Local LLM path, safety guards, and live stage telemetry.

```mermaid
flowchart LR
    W["Durable Worker<br/>(app/worker.py)"]
    RAG["Process 4.0<br/>Cached Hybrid RAG"]
    LLM["Local Ollama LLM"]
    Jobs[("D1: Jobs & Events")]
    Tickets[("D2: Tickets & Audit")]

    P31(("3.1<br/>JWT Verify &<br/>Normalize/Redact"))
    P32(("3.2<br/>Classifier<br/>Specialist"))
    P33(("3.3<br/>Evidence<br/>Context Assembly"))
    P34(("3.4<br/>Resolution<br/>Specialist"))
    P35(("3.5<br/>Reviewer<br/>Specialist"))
    P36(("3.6<br/>Deterministic<br/>Policy Guard"))
    P37(("3.7<br/>Persist Review<br/>Ticket"))

    W -->|"POST /webhook/relaydesk-intake<br/>(HS256 JWT)"| P31
    P31 -->|"Validated text, flags,<br/>mode (demo / live)"| P32
    P31 -.->|"stage: classifying"| Jobs

    P32 <-->|"Live mode: Tool Agent<br/>+ Structured Parser"| LLM
    P32 -->|"category, priority, summary"| P33
    P32 -.->|"stage: retrieving"| Jobs

    P33 -->|"POST /internal/retrieve"| RAG
    RAG -->|"Ranked citations +<br/>cache diagnostics"| P33
    P33 -->|"Context + citations"| P34
    P33 -.->|"stage: drafting"| Jobs

    P34 <-->|"Live mode: JSON Tool Agent<br/>(Demo: extractive draft)"| LLM
    P34 -->|"Draft response, steps,<br/>validated citation_ids"| P35
    P34 -.->|"stage: reviewing"| Jobs

    P35 <-->|"Live mode: Independent<br/>verification verdict"| LLM
    P35 -->|"Draft + review flags"| P36
    P35 -.->|"stage: persisting"| Jobs

    P36 -->|"Checks: hazard, injection,<br/>untrusted source, unsafe cmd,<br/>inline citations, location"| P37
    P37 -->|"POST /internal/tickets<br/>(idempotent request_id)"| Tickets
    P37 -->|"Ticket JSON response"| W
```

---

## Level 2 DFD — Processes 5.0 & 6.0 (Approval, Outbox & Idempotent Handoff)

```mermaid
flowchart LR
    Op["Support Operator"]
    D2[("D2: Tickets & Audit")]
    D4[("D4: Durable Outbox")]

    P51(("5.1<br/>Inspect Evidence,<br/>Edit & Approve"))
    P52(("5.2<br/>Atomic SQLite<br/>Approval Txn"))
    P61(("6.1<br/>n8n Handoff<br/>Workflow (02)"))
    P62(("6.2<br/>Idempotent Receipt<br/>Processor"))
    P53(("5.3<br/>Operator<br/>Resolution"))

    Op -->|"Edited response +<br/>current ticket version"| P51
    D2 -->|"needs_review ticket<br/>(automation_allowed=true)"| P51
    P51 -->|"Validated approval"| P52
    P52 -->|"status=approved, version+1,<br/>audit: approved"| D2
    P52 -->|"Insert 1 pending event<br/>(UNIQUE ticket_id)"| D4

    Op -->|"POST /api/automations/run"| P61
    D4 -->|"GET /internal/handoff/pending"| P61
    P61 -->|"POST /internal/handoff/receipt<br/>(event_id, execution_id)"| P62
    P62 -->|"status=delivered,<br/>newly_delivered flag"| D4
    P62 -->|"audit: handoff_delivered<br/>(once only)"| D2

    Op -->|"Resolution note +<br/>approved version"| P53
    D2 -->|"approved ticket"| P53
    P53 -->|"status=resolved, version+1,<br/>audit: resolved"| D2
```

---

## Data Dictionary & Trust Boundaries

### External Entities
| Entity | Role | Trust Level |
|---|---|---|
| **Employee / Support Visitor** | Submits IT issue reports via portal text or browser Web Speech dictation; receives reviewed response and optional TTS audio. | Untrusted input (redacted, length-bounded, injection-checked). |
| **Support Operator** | Inspects tickets, evidence, agent trails, and job timelines; edits drafts; approves/resolves tickets; governs custom knowledge procedures. | Local trusted operator (loopback + optional `X-Portal-Key`). |
| **Local Ollama LLM** | Provides local inference (`llama3.2:3b`) for Classifier, Resolution, and Reviewer n8n AI Agents in Live mode. | Untrusted output (schema-validated, citation-checked, policy-guarded). |
| **Optional IMAP Mailbox** | Optional disabled-by-default email intake (`03-email-optional.json`). | Untrusted input (no verified location; always blocked pending review). |

### Persistent Data Stores (SQLite WAL — `/data/relaydesk.db`)
| Store | Tables | Responsibility |
|---|---|---|
| **D1: Jobs & Job Events** | `jobs`, `job_events`, `workers` | Durable async dispatch queue, lease tokens, worker heartbeats, bounded retry schedule, and live stage event history. |
| **D2: Tickets & Audit Trail** | `tickets`, `audit` | Request deduplication (`request_id`, `input_hash`), optimistic versioning (`version`), lifecycle states (`needs_review` → `approved` → `resolved`), and immutable audit records. |
| **D3: Procedure Library & Revision** | `knowledge`, `metadata` | Built-in fictional procedures + custom operator procedures, review trust flags (`trusted`), and monotonic `knowledge_revision` counter for automatic RAG cache invalidation. |
| **D4: Durable Outbox** | `outbox` | Atomically queued post-approval handoff events (`UNIQUE ticket_id`), retry counts, n8n execution IDs, and idempotent delivery timestamps. |

### Key Security & Reliability Boundaries
1. **Pre-Ingress Redaction & Short-Lived JWTs:** Sensitive patterns (`password`, `passcode`, `recovery code`, `token`) are masked before enqueueing and again inside n8n. Service-to-n8n webhook requests use 30-second HS256 JWTs instead of transmitting reusable secrets.
2. **No Autonomous Action Tools:** Specialist agents only have a read-only procedure-retrieval tool. They cannot approve tickets, send external messages, unlock accounts, or run commands.
3. **Human-in-the-Loop Atomic Gate:** Approval requires matching `version`, `grounded=true`, non-empty `citations`, and `automation_allowed=true` inside a `BEGIN IMMEDIATE` SQLite transaction.
