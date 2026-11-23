# Technical research and original problem selection

Reviewed 23 November 2026. The project direction follows the user's correction: an original capstone, primarily implemented in n8n, with Docker and a browser alternative to Telegram. No hackathon statement or civic-reporting source is used in this deliverable.

## Original problem statement

Small organizations receive IT support requests in inconsistent language, while useful procedures live in separate documents. A ticket form records the issue but leaves the operator to classify it, find the procedure, draft a reply and decide what happens next. A generic chatbot may answer without revealing its sources or without separating suggestions from authorized actions.

Build a local support workbench that turns text or optional speech into an inspectable, evidence-backed draft and a human-reviewed handoff. Evaluate retrieval, routing and workflow integrity with explicit synthetic cases. This problem statement is our design hypothesis, not a claim established by a user study or a unique invention of IT support automation.

## Alternatives considered

| Direction | Strength | Tradeoff | Decision |
|---|---|---|---|
| Voice IT support and procedure retrieval | Natural fit for RAG, specialist agents, approvals and automation; testable without third-party accounts | Production guidance needs real reviewed procedures and user identity | Selected |
| Personal research briefing assistant | Strong RAG and summarization | Less meaningful approval/outbox workflow | Not selected |
| Emergency guidance assistant | Strong social use case | High-stakes advice and live data would require validation beyond this capstone | Not selected |

## Why n8n owns orchestration

The n8n AI Agent node combines a chat model with tools; its native Ollama integration uses LangChain. The workflow canvas can expose branches, tool access, model stages and persistent handoff steps to a reviewer. RelayDesk uses three bounded specialists with read-only tools, structured output validation and deterministic checks around them. A small Python service supplies retrieval and storage rather than acting as a hidden agent orchestrator.

The official starter kit demonstrates composing n8n with a local model and supporting services. RelayDesk adopts that deployment pattern independently, using a much smaller BM25 corpus and SQLite instead of claiming a production vector-search architecture. It does not copy the starter kit's application workflows.

## Primary sources

- [n8n AI Agent documentation](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/): chat-model and tool connections. Three native AI Agent nodes are present in the exported intake workflow.
- [n8n Ollama Chat Model](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.lmchatollama/): local-model node and configuration.
- [n8n Structured Output Parser](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.outputparserstructured/): typed output boundary. Malformed responses still trigger a visible blocked fallback.
- [n8n server CLI](https://docs.n8n.io/deploy/host-n8n/configure-n8n/use-the-command-line.md): import and publish versioned workflow exports. Setup was tested on n8n 2.48.7, not inferred from an older activation command.
- [n8n Docker installation](https://docs.n8n.io/hosting/installation/docker/): self-hosted container setup and persistence.
- [n8n webhook node](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/): authenticated production webhook entry points.
- [LangChain retriever interface](https://reference.langchain.com/python/langchain-core/retrievers/): the retrieval sidecar implements a real LangChain BaseRetriever over procedure Documents.
- [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) and [SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis): browser capability detection and platform limitations.

## GitHub inspiration

| Repository | Useful study area | What is included here |
|---|---|---|
| [n8n self-hosted AI starter kit](https://github.com/n8n-io/self-hosted-ai-starter-kit) | Docker-based local AI and n8n service composition | Independent Compose implementation; no starter workflows copied |
| [n8n](https://github.com/n8n-io/n8n) | Native AI nodes, tools, workflow exports and execution model | Pinned n8n container; its own license applies |
| [LangChain](https://github.com/langchain-ai/langchain) | Documents, retrievers and structured AI interfaces | langchain-core dependency in the retrieval service |
| [Ollama](https://github.com/ollama/ollama) | Self-hosted chat-model serving | HTTP integration; no model weights bundled |

Repository availability is not a security or maintenance guarantee. Review the licenses before redistributing dependencies. The original RelayDesk source is MIT licensed; dependency and model licenses remain separate.

## Research limits

No interviews, workload measurements or production pilot were performed. There is no measured claim about reducing support cost or improving resolution times. The synthetic evaluation demonstrates software behavior on a small disclosed dataset; it cannot establish real-world answer correctness or multilingual quality.
