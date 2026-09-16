# Quickstart Validation Guide

This guide validates the pilot design described in [plan.md](plan.md), [data-model.md](data-model.md), and [contracts/chat-api.md](contracts/chat-api.md). It is a run guide, not an implementation recipe.

## Prerequisites

- Docker Engine and Docker Compose
- Python 3.12 with `pytest` for backend tests
- Node.js 20+ with npm for frontend tests
- A configured model-provider endpoint and API key for answer-generation tests
- A seeded test corpus containing at least one approved current source, one expired source, one conflicting pair, one campus-specific source, and one escalation destination

## Start the pilot stack

From the repository root:

```bash
docker compose up --build -d
```

Verify service health:

```bash
curl --fail http://localhost:8000/api/health
```

Expected response:

```json
{"status":"ok","database":"ok"}
```

## Validate the contract

Validate the OpenAPI document with an OpenAPI 3.1 validator, then send a supported question:

```bash
curl --fail http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"When is the registration deadline for Fall 2026?"}'
```

Expected behavior: `response_state` is `answer` only when an eligible source supports the requested term and campus; the response includes at least one backend-generated citation with the exact official URL.

## Required behavior checks

1. Ask a campus-specific question without a campus. Expect `clarification`; no campus-specific policy answer is returned.
2. Ask about a future term with no approved source. Expect `refusal` and an appropriate escalation destination.
3. Seed two conflicting eligible sources and repeat the question. Expect `refusal`; the service must not choose one silently.
4. Mark a source expired or inaccessible and repeat its question. Expect `refusal` or escalation; the expired excerpt must not reach generation.
5. Ask for a personalized registration or graduation decision. Expect general information only plus escalation; no student record is accessed.
6. Ask a follow-up using the active anonymous session. Expect the retained campus, term, topic, and source context to be applied without sending a `context` object in the request JSON or receiving campus and term fields in the response JSON.
7. Submit an oversized message and exceed the anonymous rate limit. Expect `400` and `429` respectively.
8. Load the React widget from an allowlisted origin and a non-allowlisted origin. The former may call `/chat`; the latter must be rejected by CORS.

## Automated validation

Run backend tests:

```bash
pytest backend/tests
```

Run frontend tests:

```bash
cd frontend
npm ci
npm test -- --run
```

Run browser scenarios against the running Compose stack:

```bash
npx playwright test tests/e2e
```

Run the fixed evaluation set containing at least 100 supported questions plus unsupported, conflicting, stale, personalized, campus-ambiguous, and out-of-scope cases. Record citation correctness, safe-refusal rate, context preservation, first validated response latency, and complete response latency. The pilot must meet the spec thresholds SC-001 through SC-007 before release.

## Stop the stack

```bash
docker compose down
```

Use `docker compose down -v` only when intentionally deleting the local PostgreSQL test volume.
