# Verification record

Verified locally on 23 November 2026. See `BUILD_LOG.md` for stage decisions and review fixes. This is a local capstone release, not a production-readiness certification.

## Automated checks

| Layer | Verification | Scope |
|---|---|---|
| Python service | 20 passing pytest tests | Persistence, retrieval, request bounds, internal/portal authentication, cross-origin writes, request deduplication, approval versions, outbox integrity, receipts, full history export and signed/redacted ingress |
| Workflow logic | 19 passing Node tests | Routing, abstention, invalid citations, JSON fallback, untrusted sources, redaction, hazard boundary, summary validation, email batching, known-reference formatting, native agent connections and interrupted-bootstrap recovery |
| Docker | Compose configuration, image build and health checks | n8n 2.48.7 and data/portal service on loopback ports |
| Real n8n integration | Ten demo cases, lifecycle and boundary scripts | Actual published webhooks and HTTP calls, not mocked orchestration |
| Local LLM | One recorded normal-support run with three model stages | Host Ollama 0.40.17, model llama3.2:3b; no fallback flags in final run |
| Trigger-data inspection | Direct read of this project's n8n SQLite data | Confirmed no reusable service key or original synthetic password in the final retained trigger payload |

Coverage is a service-code measure, not agent-answer quality. The recorded service coverage run including the signed ingress module was 91%; the final additional regression verifies punctuation, metadata and length preservation in redaction. No blanket coverage claim is made for the JavaScript UI.

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
