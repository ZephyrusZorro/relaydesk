# Verification record

Verified locally on 23 November 2026. See `BUILD_LOG.md` for stage decisions and review fixes. This is a local capstone release, not a production-readiness certification.

## Automated checks

| Layer | Verification | Scope |
|---|---|---|
| Python service | 29 passing pytest tests (86% coverage) | Persistence, durable SQLite job queue, concurrent claims, lease expiry audit events, retry bounds, versioned cached hybrid lexical retrieval, custom procedure trust review & deletion with cache invalidation, request bounds, internal/portal authentication, cross-origin writes, request deduplication, approval versions, outbox integrity, receipts, full history export and signed/redacted ingress |
| Workflow logic | 19 passing Node tests | Routing, abstention, invalid citations, JSON fallback, untrusted sources, redaction, hazard boundary, summary validation, email batching, known-reference formatting, native agent connections, all 4 workflow persistence checks and interrupted-bootstrap recovery |
| Docker | Compose configuration, image build and health checks | `desk`, independent `worker`, and `n8n` 2.48.7 services on loopback ports |
| Real n8n v2 integration | `scripts/v2-smoke.py --live` & `scripts/verify-boundaries.py` | Authenticated website-to-n8n handshake (`RelayDeskStatus01`), durable worker → n8n Demo (~1.0 s) and Local LLM (~6.6 s) end-to-end runs with all live stage callbacks, retrieval cache hit verification, 4000-char/secret/hazard/expired-JWT/concurrent-handoff boundaries |
| Local LLM | Real 3-agent local execution verified via durable worker | Host Ollama 0.40.17, model `llama3.2:3b`; classifier, resolver and reviewer completed with zero fallback flags |
| Trigger-data inspection | Direct read of this project's n8n SQLite data | Confirmed no reusable service key or original synthetic password in the final retained trigger payload |

Coverage is a service-code measure, not agent-answer quality. The v2 Python service coverage run is 86% across 12 modules (`tests/test_jobs.py` + `tests/test_service.py`). Retrieval benchmark (`docs/v2-benchmark.json`) measured a 6.7× query speedup with the versioned cache (0.98 ms cached vs 6.63 ms uncached). No blanket coverage claim is made for the JavaScript UI.

## Browser checks

- Loaded the actual container-served portal and confirmed connected n8n status.
- Submitted a request in the browser and inspected its source excerpt.
- Edited and approved the response, then ran the n8n handoff and observed the internal delivery receipt.
- Confirmed a custom procedure is persisted and displayed as unreviewed, including literal angle brackets rendered as text.
- Checked desktop layout at a 1,440-pixel viewport and mobile at 390 pixels; the document did not overflow horizontally.
- Checked the mobile intake dialog bounds and its scrollable content.
- Verified the optional shared-key portal through a separate local test instance: one in-page access form, visible blank-key validation and successful access with the configured test key. Native blocking prompts were replaced with in-page controls.
- Exercised the supplied Windows launcher and a simulated interrupted-publication marker. Ordinary startup preserved existing workflows; recovery imported and published only the pending core workflow.
- Invoked Read aloud and checked its visible feedback; cancellation is handled separately from playback errors. Microphone recording, recognition quality and audible output still require a user's browser/OS check.
- Verified a maximum-length report ending in a short labeled secret, punctuation-bearing metadata redaction, and rejection of an expired webhook JWT through the running n8n service.

Screenshots: `screenshots/desktop.jpg`, `screenshots/mobile-intake.jpg` and `screenshots/agent-trail.jpg`.

## Independent review

A fresh-context reviewer inspected the full source and pinned n8n node behavior. Material findings were addressed with regression tests: long reports, category-filter ordering, consistent hazard handling, complete IMAP batches, stable email IDs, restart preservation, pending-count/export pagination, transition-based handoff counts, classifier summary validation and portal access recovery.

Further execution-data inspection found that disabling full n8n logs still retains trigger data. The final design therefore redacts before ingress, uses 30-second JWTs and rotates the previous service secret. Detailed execution retention remains disabled; retained trigger data and optional email privacy limits are documented.

## Remaining configuration and verification limits

- The user creates their own n8n editor owner account on first visit. Core webhooks are already published by setup.
- The optional IMAP workflow was structurally tested with a 20-item batch and is disabled. No mailbox credentials or real email sends were used.
- The optional all-container Ollama profile was not exercised; the host Ollama server was used successfully.
- Procedures and seeded people are fictional. Real employee use needs approved guidance, identity, authorization and retention work.
- Model review and source-ID validity do not prove semantic correctness. Human review remains mandatory.
