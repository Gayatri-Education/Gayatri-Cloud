# AI Provider Integration and Model Routing

**Status:** Proposed behavior contract. Native API details must be verified against current official provider documentation during implementation. Do not assume model names, endpoint fields or catalogue behavior remain static.

## 1. Goals

- Support multiple API providers without binding the tutor to one vendor.
- Let individual users connect personal credentials and organizations supply shared/provider-managed credentials, subject to policy.
- Keep keys server-side and identify the payer/key owner for each execution.
- Discover models where possible, verify runtime eligibility, and choose the highest-ranked eligible model for each task.
- Offer a manual selector and explain automatic selection/fallback.
- Prevent an unavailable or newly released model from silently becoming an untested default.

## 2. Provider adapter contract

Each adapter should expose a stable internal interface for:
- credential validation/connection test;
- model catalogue discovery when supported;
- capability metadata and catalogue freshness;
- request normalization (messages, system/developer context, output limits, tools/structured output where supported, response format, cancellation/timeout);
- response normalization (text/tool calls/usage/finish status/provider request ID);
- error normalization (authentication, authorization, quota, billing, rate limit, timeout, invalid model, unsupported capability, content refusal, provider outage);
- retry guidance and retry-after information;
- reported usage/cost metadata when available;
- redacted health diagnostics.

Initial provider families: OpenAI, Google Gemini, Anthropic Claude, xAI Grok, OpenRouter and configurable OpenAI-compatible custom endpoints. Add other providers with dedicated adapters or documented compatibility. Never imply every provider implements every capability.

## 3. Provider and model catalogue

Catalogue entries should include provider/model ID, display label, known version/date/lifecycle, observed availability, context limits if reliably documented, input/output modality, tool/function calling, structured-output support, streaming support, languages/benchmark results, rate/cost metadata where available, source/time of observation and staleness.

Discovery is not proof of access. After discovery, the selected account may need an explicit capability request. Catalogue APIs can omit restricted models, return aliases, lack lifecycle detail or expose preview models. For providers without discovery, support an administrator/user-configured model ID and validate it with a minimal safe request.

Do not hard-code a forever-current list. Catalogue refreshes must be rate-limited, cached, observable and tolerant of provider schema changes. Preserve last known data with an “observed at” timestamp; do not treat stale availability as guaranteed.

## 4. Eligibility filtering

Before ranking, reject a model if any mandatory condition fails:
- key or model access is invalid;
- provider/model is disabled by platform/organization policy;
- data transfer violates current privacy, consent or region/provider policy;
- task requires a capability the model lacks;
- context budget cannot fit the task after safe compaction;
- model is not approved for production routing;
- cost or latency violates an approved hard ceiling;
- known provider health/rate constraints make request inappropriate.

Never route to a provider with a credential that the current user/organization is not authorized to use. Never fall back across key owners/payers silently when this would incur another party's cost or violate data policy.

## 5. Task-aware ranking

Define task types such as concept explanation, Socratic hint, worked-example generation, response evaluation, grading support, lesson planning, multilingual response, long-source synthesis and tool-assisted calculation. The routing policy should use the task's requirements and a maintained tutoring benchmark.

Recommended approach:
1. Apply hard eligibility/privacy/capability filters.
2. Rank remaining models using task-specific benchmark quality and current reliability.
3. Apply approved policy for latest-version preference, cost and latency. “Newest” is a preference, not proof of educational superiority.
4. Use a model only if benchmark/approval status is current enough under the release policy.
5. Record selection reason and policy version.
6. Support manual choice from eligible models. Explain when a manual selection is incompatible with a task or policy.

Cost and latency ceilings, the meaning of “latest”, benchmark minimums and model-pinning behavior remain open under DEC-009. Do not fabricate benchmark scores.

## 6. Benchmark design

Use a version-controlled, curriculum-independent evaluation set across multiple subjects, grade levels, languages and tutoring methods. Include:
- factual correctness and supported uncertainty;
- course-source grounding and citation fidelity;
- pedagogical appropriateness (scaffold rather than prematurely reveal answers when required);
- adherence to instructor/course/session hierarchy;
- student-answer evaluation consistency;
- multi-turn coherence and context handling;
- multilingual output quality;
- refusal and safe handling of unsupported requests;
- tool-call correctness and schema compliance where tools exist;
- latency/reliability and cost under a repeatable workload.

Evaluation needs deterministic test cases plus human review for qualities that are not robustly machine-gradable. Dataset contamination, version changes and known limits must be documented. Benchmark pass thresholds and model promotion approvers require approval before production promotion.

## 7. Fallback and failure handling

- Invalid credential: stop for that credential; do not repeatedly retry. Offer revalidation/change.
- Quota/rate limit: honor provider retry-after when appropriate; try an alternative only if policy allows and the alternate key owner/payer is clear.
- Timeout/outage: bounded retry for transient errors, then eligible fallback if allowed; tell the user when provider/model changes.
- Unsupported capability: select an eligible capable model or ask the user; do not silently drop required tool/format behavior.
- Privacy/policy denial: fail closed; never fallback to an unapproved provider.
- Malformed response: validate and bounded-retry when safe; don't commit learning state until response validation passes.
- All provider attempts should share a correlation ID but have distinct attempt IDs and normalized failure categories.

## 8. Credential lifecycle and UI

Allow users/organizations to add key name, provider, secret, optional custom base URL and policy scope. Secrets are submitted over TLS, stored encrypted server-side, and never returned raw. Show masked labels, last validated time, status and payer/owner. Offer re-test, rotate and revoke. Log changes without recording secret value.

Custom endpoint validation must enforce SSRF defenses and controlled outbound networking. Permit only explicitly supported protocol/compatibility contracts. Do not allow arbitrary URL, redirect or DNS resolution to access internal resources.

## 9. Usage reporting and controls

Record available provider-reported usage/cost alongside estimates, key owner, user, organization, session, model, task, policy version and fallback attempts. State clearly whether usage/cost is provider-reported, estimated or unavailable. Provider remains the primary bill/quota authority per current owner direction. Gayatri-level hard limits/throttling are open (DEC-010); expose warnings and policy guardrails but do not claim an unenforced quota exists.

## 10. Implementation/test gate

Test every adapter using fixtures and mocked provider responses; test model-list pagination, empty catalogue, stale catalogue, unknown model, invalid key, revoked key, rate limit, timeout, malformed output, tool capability mismatch, streaming disconnect and fallback policy. Integration tests using real APIs must be opt-in, low-volume and separately authorized. CI must never need a paid provider credential.
