# Evaluation

The machine-readable final run is in `evaluation-results.json`; edge-case integration checks are in `boundary-results.json`. All requests were synthetic. These results validate the implemented paths, not production usefulness or answer accuracy on a real support workload.

## Deterministic baseline through real n8n

Ten synthetic paraphrases were submitted through the portal API, the authenticated n8n webhook and the actual retrieval/storage services. Eight describe supported categories; two are outside the procedure corpus. The queries differ from the seeded example tickets, but share the expected support vocabulary. This is not a blinded or independent benchmark.

| Check | Result | Sample |
|---|---|---|
| Expected category | 10 / 10 | Eight support requests and two out-of-domain requests |
| Expected source in top three | 8 / 8 | Supported cases only |
| Abstention without citations | 2 / 2 | Out-of-domain questions |
| Duplicate intake preserves ticket ID | 10 / 10 | Same request ID and normalized input repeated |
| Create → approve → hand off → resolve | Passed | One complete lifecycle |
| Repeated approval | Rejected | Current version required |
| Repeated empty handoff run | Zero deliveries | No pending events |
| Injected instruction requesting approval | Blocked | One integration example plus unit tests |

## Real local model run

The final recorded normal-support run used Ollama `llama3.2:3b`, through all three native n8n AI Agents. It returned a VPN source reference, three model-stage trace summaries and no fallback flags. The final run took approximately **6.2 seconds** on this machine with the model already warm and GPU acceleration available. This is one observation, not a latency percentile or a hardware-independent performance claim.

The output remains a draft. Even a response that passes the reviewer may have awkward wording or an unsupported nuance; the operator must inspect it. During development, small-model formatting failures motivated explicit schemas, resolver JSON mode and validated source-ID formatting. Unknown references, malformed output and model errors still block handoff rather than being silently accepted.

The separate live hazard case deliberately bypasses ordinary resolution and produces a blocked, fixed escalation draft. It is not included as another successful troubleshooting-quality sample.

## Boundary checks

- A full 4,000-character report reaches the procedure retriever and persists a ticket.
- Detected equipment hazards withhold routine reconnection or repair steps in both demo and live paths.
- A known secret pattern is redacted before the webhook and storage.
- Two concurrent handoff runs report one new delivery in total.
- Unauthenticated receipt calls are rejected.
- Expired ingress JWTs are rejected by n8n. Punctuation-bearing labeled values in metadata are redacted, and a short labeled secret does not expand a valid maximum-length report beyond the workflow limit.
- Larger-outbox unit coverage verifies that 101 approvals remain discoverable and exportable.
- Category-filter regression coverage ensures higher-ranked off-category chunks cannot hide all matching in-category evidence.

The pinned n8n release retains minimal trigger payloads despite disabling full execution logs. A direct local database inspection confirmed that the final ingress design's retained trigger payload contained neither the reusable signing/service secret nor the original synthetic password. The design uses short-lived JWTs and pre-webhook redaction; it does not claim that all sensitive strings can be detected or that trigger data is absent.

## Limits

Five seeded procedures and one browser-ingested custom fixture are a small corpus. BM25 does not solve semantic retrieval. English-first routing was tested; a Hindi dictation option does not establish Hindi model, corpus or retrieval quality. No load test, user study, accessibility certification, production deployment or live mailbox evaluation was performed. The optional Ollama container tag was verified to exist, but final LLM testing used the host model server.
