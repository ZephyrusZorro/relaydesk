# RelayDesk implementation plan

> Execute inline using the executing-plans workflow. The user delegated selection and implementation in one prompt; subsequent instructions establish n8n-first, Docker and no Telegram.

**Goal:** Deliver an original n8n-driven voice support capstone with tested, persistent operator workflows.

**Architecture:** n8n visual workflows orchestrate bounded specialist agents using native LangChain nodes. FastAPI supplies storage, a LangChain BM25 retriever and a same-origin browser portal. SQLite persists state. Docker Compose runs the services.

**Spec:** `docs/DESIGN.md`

## Constraints and review focus

- No hackathon-derived product statement and no Telegram integration.
- Secrets live only in ignored environment files; shared service authentication is required.
- Demo rules and live model execution must be visibly distinct.
- Knowledge is context, never executable instructions; no evidence means abstain.
- Duplicate ingestion, stale approvals, retried handoffs, invalid model JSON and injected content need explicit tests.
- Local single-user portal is not production identity management.

## Stage 1 — Data, retrieval and approval integrity

Create `app/{config,schemas,store,knowledge,corpus,main}.py` and `tests/test_service.py`.

- [x] Write and run failing tests for relevant-source retrieval, unknown topics, validation, persistence, duplicate IDs, stale approvals, auth and atomic outbox creation.
- [x] Implement storage/retrieval endpoints and constrained internal contracts.
- [x] Run the full Python suite and commit the verified stage.

## Stage 2 — n8n agent orchestration

Create `workflows/logic.mjs`, `scripts/build-workflows.mjs`, exported JSON and `tests/workflow.test.mjs`.

- [x] Write and run failing JS tests for routing, safe demo drafts, citation rejection, model fallback and prompt-like inputs.
- [x] Implement native n8n classifier, resolver and reviewer nodes, branching, retrieval, deterministic guard, persistence and HTTP response.
- [x] Create a separate approved-handoff workflow and optional disabled email intake.
- [x] Execute JS and Python suites; import workflows into Docker n8n and exercise real webhooks. Commit the stage.

## Stage 3 — Portal, speech and container experience

Create `app/static/*`, `Dockerfile`, `compose.yaml`, startup/setup scripts and browser smoke tests.

- [x] Implement a responsive queue, new request/chat portal, detail view, agent/evidence panels, editable approval, knowledge ingestion/search, handoff history and export.
- [x] Add feature-detected browser speech input/output with explicit unavailable states.
- [x] Build containers; verify create-to-resolve in n8n and portal at desktop/mobile widths.

## Stage 4 — Evaluation, review and handover

- [x] Run held-out synthetic retrieval/routing examples and real Ollama specialist execution; publish exact sample counts and limits.
- [x] Obtain a fresh-context review under requesting-code-review, fix material findings with regression tests and rerun verification.
- [x] Provide README, architecture, original problem statement, technical research/references, demo script, verification report and clean source ZIP. Keep staged local Git commits.

