# Five-minute demo and viva guide

## The problem, in one sentence

RelayDesk turns an unstructured IT support request into an inspectable, evidence-backed draft and a human-approved n8n handoff.

## Demonstration

**First minute — inspect the workflow.** Open the n8n editor and create your owner account if necessary. Open **RelayDesk · intake and specialist agents**. Point out the demo/live branch, three native agents, their read-only tools, the retrieval request, validators and final ticket write. Explain that processing cannot silently move to a hidden Python agent if n8n is down.

**Second minute — submit a request.** In the portal, choose **New request**, enter a location and select **VPN drops**. Demo mode is fast and credential-free. For a real model demonstration, use **Local LLM** after confirming Ollama is running with the configured model. Describe the progress indicator as a waiting state; it does not pretend to stream individual stages.

**Third minute — examine the evidence.** Open **Evidence** and show the source ID, excerpt, review status and fictional-demo label. Open **Agent trail**. Distinguish model, retrieval, deterministic guard and sample-fixture stages. Trace summaries describe operations; they do not reveal hidden chain-of-thought.

**Fourth minute — approve a response.** Edit a draft if needed, then approve it. Show that approval creates an outbox row and audit entry. In **Automations**, run pending handoffs and show the internal receipt. Re-running with no pending events does not claim to deliver another event.

**Fifth minute — show boundaries.** Submit an out-of-domain question and show abstention. Explain that equipment hazards and injected instructions block handoff. In **Knowledge**, add an unreviewed procedure and inspect retrieval. Show the separate optional email workflow, disabled until configured.

## Useful viva questions

**Why three agents?** Classification, evidence-based drafting and review have different tasks and prompts. Separate boundaries make their outputs inspectable. This adds latency and does not guarantee accuracy; a single-agent baseline would be a useful next experiment.

**Is this really multi-agent?** It uses three native n8n Tools Agent nodes with separate model connections, bounded iterations and read-only procedure tools. They are coordinated sequential specialists, not unconstrained agents taking independent operational actions.

**Where is LangChain?** n8n's native agent and Ollama nodes use its LangChain integration. The retrieval service also implements an actual LangChain BaseRetriever over Document objects. Python does not orchestrate the specialist model stages.

**Why BM25 rather than embeddings?** The small procedure corpus needs no model download or API key for retrieval. BM25 provides a transparent baseline and stable source IDs. It struggles with synonyms and is not semantic search. A meaningful extension is to compare a hybrid embedding retriever against this baseline on a larger labeled dataset.

**How does RAG reduce unsupported answers?** Retrieval supplies source text and IDs. The resolver declares references, the validator rejects unknown IDs, the reviewer checks the answer, and the operator sees the excerpt. These checks reduce specific failure modes; they do not prove that every statement follows from the evidence.

**What prevents duplicate actions?** Unique request IDs, version-checked approval, one outbox row per ticket, SQLite transactions and an idempotent receipt transition. Concurrent network runs can retry safely without creating duplicate local receipts. External exactly-once delivery is not claimed.

**What happens when the model fails?** An explicit fallback/validation finding appears and handoff is blocked. The operator can inspect the evidence and submit a corrected request. Demo mode is always labeled and never presented as live model execution.

**Why is approval outside the model?** The model has no operational write tool. An explicit operator action checks the current ticket version and writes approval plus the outbox event atomically. A prompt cannot skip that transaction.

**Does the project solve identity or production security?** No. It is a loopback single-user capstone with optional shared-key portal access. Production use needs real identity, authorization, retention controls, audit access, approved procedures and load evaluation.

## Honest future work

- Resident/employee identity and authorization with private per-user ticket views.
- Larger real, reviewed procedure corpus and human-labeled answer evaluation.
- Hybrid semantic retrieval, query rewriting and reranking with an explicit baseline comparison.
- Reviewed external connectors for ticket systems or email notifications, with delivery receipts and retry semantics.
- Provider-specific mailbox reliability and an audio ingestion/transcription pipeline with privacy controls.
- Multilingual corpus and routing evaluation; Hindi dictation alone does not make the system multilingual.
