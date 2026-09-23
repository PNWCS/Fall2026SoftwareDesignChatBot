<!-- markdownlint-disable MD024 -->

# Chat API Contract

This document describes the public backend endpoint contract for the PNW Student Information Chatbot pilot. The contract is intentionally written as Markdown instead of YAML so the feature docs remain easy to review alongside the plan and data model.

## Base URL

Production and pilot deployments expose the backend at:

`https://chat.example.pnw.edu/api`

## Health Endpoint

### GET /api/health

Checks whether the API and its database dependency are available.

#### Request

- No request body
- No authentication required

#### Successful response (200 OK)

```json
{
  "status": "ok",
  "database": "ok"
}
```

#### Failure response

- `503 Service Unavailable`: backend cannot reach the configured database

---

## Chat Endpoint

### POST /api/chat

Submits an anonymous student question for grounded answer generation, clarification, refusal, or controlled error handling.

#### Headers

- `Content-Type: application/json`

#### Request body

```json
{
  "message": "When is the registration deadline for Fall 2026?"
}
```

#### Request fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `message` | string | Yes | Plain-language student question; 1-4000 characters |

The backend must not require the student to provide structured campus, term, or program context in the request JSON. It must infer context from the question when safe, ask a clarification question when needed, and retain accepted follow-up context only in short-lived server-side session memory. It must never accept or persist student account identifiers, raw IP addresses, or other personal data beyond minimal anonymous context needed for a response.

#### Successful response (200 OK)

```json
{
  "response_state": "answer",
  "message": "The registration deadline for Fall 2026 is ...",
  "citations": [
    {
      "title": "Registrar Registration Deadlines",
      "url": "https://www.pnw.edu/registrar/registration-deadlines",
      "locator": "Fall 2026 registration section",
      "review_context": "Effective: 2026-01-01; reviewed: 2026-09-16"
    }
  ],
  "escalation": null,
  "conversation": {
    "conversation_id": "5f4d4a7c-57b3-457a-9d9c-c41185ba2d9e",
    "topic": "registration deadline"
  },
  "latency_ms": 1850
}
```

#### Response states

The `response_state` field must be one of the following:

- `answer`: a supported answer grounded in approved sources
- `clarification`: required context is missing or ambiguous
- `refusal`: the information is unavailable, conflicting, outdated, or out of scope
- `error`: controlled backend failure or malformed request handling

#### Response fields

| Field | Type | Notes |
|---|---|---|
| `response_state` | string | Required |
| `message` | string | Human-readable answer or refusal text |
| `citations` | array | One or more official citations; empty only for explicit non-answer states when no source could be used |
| `escalation` | object or null | Official office or advisor recommendation when known |
| `conversation` | object | Opaque short-lived anonymous session handle and topic for follow-up handling; campus and term are not returned |
| `latency_ms` | integer | Total backend processing time in milliseconds |

#### Error responses

- `400 Bad Request`: invalid JSON or empty or oversized message
- `429 Too Many Requests`: anonymous rate limit exceeded
- `503 Service Unavailable`: retrieval or generation dependency failed

#### Required behavior

1. The backend must only answer using approved and active sources from the pilot corpus.
2. The backend must return `clarification` when campus, term, or program context materially affects the answer and cannot be safely inferred from the question or existing session memory.
3. The backend must return `refusal` if the evidence is missing, conflicting, stale, or outside scope.
4. The backend must use citations generated server-side from approved source records; it must not trust model-generated URLs.
5. The backend must preserve short-lived anonymous conversation context only in memory for follow-up interpretation; campus and term must not be exposed in the response JSON.

---

## Citation Object

```json
{
  "title": "Registrar Registration Deadlines",
  "url": "https://www.pnw.edu/registrar/registration-deadlines",
  "locator": "Fall 2026 registration section",
  "review_context": "Effective: 2026-01-01; reviewed: 2026-09-16"
}
```

Each citation must identify the exact official source and review context used to support the answer.

## Escalation Object

```json
{
  "office_name": "Office of the Registrar",
  "service_description": "Handles registration, dates, and enrollment questions.",
  "contact_url": "https://www.pnw.edu/registrar",
  "phone": "(219) 989-2200",
  "email": "registrar@pnw.edu"
}
```

Escalation data must reference a verified official office or advisor contact and should be provided only when a reliable answer cannot be given.
