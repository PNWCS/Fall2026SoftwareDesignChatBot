---

description: "Executable implementation tasks for the PNW Student Information Chatbot"
---

# Tasks: PNW Student Information Chatbot

**Input**: Design documents from `/specs/001-pnw-student-information-chatbot/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/chat-api.md](contracts/chat-api.md), and [quickstart.md](quickstart.md)

**Organization**: Tasks are grouped by user story so each increment can be implemented and validated independently after the foundational phase.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the separate backend, frontend, database, and test project structure described by the implementation plan.

- [X] T001 Create the backend Python 3.12 project structure in `backend/pyproject.toml`, `backend/src/`, and `backend/tests/` with FastAPI, Pydantic, SQLAlchemy, Alembic, pgvector, and `google-genai` dependencies.
- [X] T002 [P] Create the React 18+ Vite TypeScript project structure in `frontend/package.json`, `frontend/src/`, and `frontend/tests/` with React Testing Library dependencies.
- [X] T003 [P] Create Docker Compose service definitions for the backend, frontend static server, and PostgreSQL/pgvector database in `docker-compose.yml`.
- [X] T004 [P] Add backend and frontend container build definitions in `backend/Dockerfile` and `frontend/Dockerfile` using non-root runtime users.
- [X] T005 [P] Add shared environment examples and local developer configuration in `.env.example`, `backend/.env.example`, and `frontend/.env.example` without storing Gemini credentials.
- [ ] T006 [P] Configure Python, TypeScript, and Markdown quality checks in `backend/pyproject.toml`, `frontend/package.json`, and `.github/workflows/ci.yml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement governance, persistence, ingestion, and security foundations required by every user story.

**Critical**: No user story work can begin until this phase is complete.

- [ ] T007 Create Alembic migration configuration in `backend/alembic.ini` and `backend/alembic/env.py`, including the PostgreSQL pgvector extension migration in `backend/alembic/versions/001_enable_pgvector.py`.
- [ ] T008 [P] Create SQLAlchemy base configuration and database session lifecycle in `backend/src/db/base.py` and `backend/src/db/session.py` with connection and query timeouts.
- [ ] T009 [P] Implement typed server configuration in `backend/src/config.py` for database URLs, allowed origins, request limits, rate limits, Gemini model settings, embedding model and dimension, source review windows, and conversation TTL.
- [ ] T010 Create relational models and migrations in `backend/src/models/source.py`, `backend/src/models/source_version.py`, `backend/src/models/source_chunk.py`, `backend/src/models/ingestion_job.py`, `backend/src/models/escalation.py`, `backend/src/models/question.py`, `backend/src/models/answer.py`, and `backend/src/models/citation.py`; enforce required fields, enum values, source/content-hash uniqueness, one active source version per source, and `embedding_dimension` matching the configured vector dimension.
- [ ] T011 Implement source-manifest validation and canonical URL registration in `backend/src/services/source_registry.py` and `backend/src/schemas/source_manifest.py`; require official source URL, owner office, source type, applicability metadata, and review window before ingestion.
- [ ] T012 Implement HTML, linked-page, PDF, form, and table extraction with heading, page, row, date, campus, term, and program preservation in `backend/src/services/extraction.py`.
- [ ] T013 [P] Implement deterministic structure-aware chunking with chunking version, ordinal, heading path, locator, applicability metadata, and effective dates in `backend/src/services/chunking.py`.
- [ ] T014 Implement configurable embedding generation and dimension validation in `backend/src/services/embeddings.py`; failed or dimension-mismatched jobs must remain ineligible for activation.
- [ ] T015 Implement transactional, idempotent source-version loading with lexical `tsvector` generation, content-hash deduplication, retryable stage state, dry-run support, and superseded-version retention in `backend/src/services/ingestion.py` and `backend/src/cli/ingest.py`.
- [ ] T016 Implement ingestion validation reports for non-empty extraction, source hash consistency, chunk coverage, metadata completeness, duplicate chunks, embedding counts, dimension match, and representative retrieval coverage in `backend/src/services/ingestion_validation.py`.
- [ ] T017 Implement source activation and rollback rules in `backend/src/services/source_activation.py`; activate only validated current versions with eligible status and review windows, and preserve the prior active version when a new version fails.
- [ ] T018 Implement governed lexical/vector retrieval in `backend/src/services/retrieval.py`; filter approved, active, current, review-valid, applicable source versions before ranking and start with exact pgvector search plus lexical matching.
- [ ] T019 Add the backend health endpoint, strict CORS allowlist, request-size validation, anonymous rate limiting, structured redacted logging, and dependency error handling in `backend/src/api/health.py`, `backend/src/middleware/security.py`, and `backend/src/main.py`.
- [ ] T020 Seed representative approved, stale, conflicting, campus-specific, and escalation data plus the source manifest in `backend/fixtures/pnw-sources.yml` and `backend/fixtures/seed_corpus.py`.
- [ ] T021 [P] Add foundational unit and integration tests for migrations, source eligibility filters, ingestion idempotency, chunk metadata preservation, embedding dimension rejection, activation rollback, and health/security controls in `backend/tests/unit/` and `backend/tests/integration/`.

**Checkpoint**: The database can be migrated and populated through the RAG ingestion workflow, and retrieval can return only eligible governed chunks.

---

## Phase 3: User Story 1 - Get a Reliable Answer (Priority: P1) MVP

**Goal**: Return concise, grounded answers to supported PNW questions with applicable campus/term context and backend-generated citations.

**Independent Test**: Ask representative parking, registration, academic standing, grade appeal, financial aid deadline, and graduation questions; verify that supported answers are accurate, contextualized, and cite the exact approved source.

### Tests for User Story 1

- [ ] T022 [P] [US1] Add `POST /api/chat` contract tests for `answer`, `clarification`, and validation response shapes in `backend/tests/contract/test_chat_api.py`.
- [ ] T023 [P] [US1] Add grounded-answer integration tests proving every answer claim uses eligible chunks and every citation is backend-built in `backend/tests/integration/test_grounded_answers.py`.
- [ ] T024 [P] [US1] Add React widget tests for question submission, loading state, answer rendering, and citation links in `frontend/tests/chat-widget.test.tsx`.

### Implementation for User Story 1

- [ ] T025 [P] [US1] Create request and response schemas in `backend/src/schemas/chat.py` with `message` required as a string of 1-4000 characters and response states limited to `answer`, `clarification`, `refusal`, and `error`.
- [ ] T026 [US1] Implement question normalization, context detection for campus, term, program, course, and deadline applicability, and retrieval query construction in `backend/src/services/question_analysis.py`.
- [ ] T027 [US1] Implement the Gemini provider boundary in `backend/src/services/gemini_client.py` using the official `google-genai` client, server-side credentials, configurable model settings, structured output, timeout handling, and no client-supplied URLs.
- [ ] T028 [US1] Implement grounded answer generation and citation validation in `backend/src/services/grounding.py`; require at least one eligible citation, reject unsupported cited chunk IDs, and build title, URL, locator, and review context from database records.
- [ ] T029 [US1] Implement the anonymous `POST /api/chat` endpoint and response mapping in `backend/src/api/chat.py` for supported answers, missing-context clarification, and controlled dependency errors according to `contracts/chat-api.md`.
- [ ] T030 [US1] Build the accessible chat widget and citation presentation in `frontend/src/components/ChatWidget.tsx`, `frontend/src/components/MessageList.tsx`, and `frontend/src/types/chat.ts`.
- [ ] T031 [US1] Connect the widget to the backend with request cancellation, error-state rendering, and no Gemini credential exposure in `frontend/src/services/chatApi.ts`.
- [ ] T032 [US1] Add the first supported-question evaluation fixture and response-latency instrumentation in `backend/fixtures/evaluation_supported.json` and `backend/src/services/metrics.py`.

**Checkpoint**: User Story 1 answers supported questions with validated citations and is independently testable without User Stories 2-4.

---

## Phase 4: User Story 2 - Know When Information Is Unavailable or Uncertain (Priority: P1)

**Goal**: Refuse unsupported, stale, conflicting, inaccessible, personalized, and out-of-scope questions safely with an appropriate escalation destination.

**Independent Test**: Ask missing, conflicting, outdated, personalized, and out-of-scope questions; verify that no unsupported answer is returned and the response explains the limitation and next step.

### Tests for User Story 2

- [ ] T033 [P] [US2] Add refusal integration tests for missing evidence, stale sources, inaccessible resources, conflicting sources, and out-of-scope questions in `backend/tests/integration/test_safe_refusals.py`.
- [ ] T034 [P] [US2] Add personalized-question tests proving no student-system lookup occurs and only general information plus escalation is returned in `backend/tests/unit/test_personalized_questions.py`.
- [ ] T035 [P] [US2] Add browser tests for refusal, clarification, escalation, malformed output, and provider timeout states in `tests/e2e/safe-failure.spec.ts`.

### Implementation for User Story 2

- [ ] T036 [P] [US2] Implement escalation destination validation and lookup in `backend/src/services/escalation.py`; require `office_name`, `service_description`, and a verified `contact_url`, with nullable phone/email and optional campus.
- [ ] T037 [US2] Implement evidence sufficiency, stale/review-window, conflict, personalization, and scope policies in `backend/src/services/safety_policy.py`.
- [ ] T038 [US2] Extend the grounding pipeline and `backend/src/api/chat.py` to return refusal responses when approved evidence is missing, conflicting, outdated, inaccessible, insufficient, or outside scope, including escalation when known.
- [ ] T039 [US2] Add malformed Gemini output, provider timeout, retrieval failure, and rate-limit mappings in `backend/src/services/error_handling.py` and `backend/src/api/chat.py` without leaking prompts, credentials, or personal data.
- [ ] T040 [US2] Add refusal and escalation rendering to `frontend/src/components/ResponseState.tsx` and `frontend/src/components/ChatWidget.tsx`.
- [ ] T041 [US2] Add the negative, stale, conflicting, personalized, and out-of-scope evaluation fixtures in `backend/fixtures/evaluation_negative.json`.

**Checkpoint**: User Stories 1 and 2 both work independently; unsafe evidence produces refusal or escalation rather than a speculative answer.

---

## Phase 5: User Story 3 - Find the Right Official Resource (Priority: P2)

**Goal**: Explain known next steps and identify the exact official page, PDF, form, portal, or office needed to complete a process.

**Independent Test**: Ask for a form, linked document, portal, department, or office contact and verify that the response identifies the specific verified destination rather than only a top-level page.

### Tests for User Story 3

- [ ] T042 [P] [US3] Add resource-discovery contract and integration tests for linked pages, PDFs, forms, portals, and office contacts in `backend/tests/integration/test_resource_discovery.py`.
- [ ] T043 [P] [US3] Add widget tests for multiple citations, locators, verified links, and escalation contact display in `frontend/tests/resource-citations.test.tsx`.

### Implementation for User Story 3

- [ ] T044 [P] [US3] Extend source and chunk schemas in `backend/src/schemas/source.py` and `backend/src/models/source_chunk.py` to retain exact linked-resource URLs, PDF page locators, table identifiers, and office ownership.
- [ ] T045 [US3] Implement verified linked-resource resolution and citation selection in `backend/src/services/resource_links.py`, rejecting inaccessible or unverified destinations.
- [ ] T046 [US3] Extend grounded response assembly in `backend/src/services/grounding.py` to summarize known procedural steps and return the specific supporting source for each resource claim.
- [ ] T047 [US3] Add resource and office destination presentation with accessible link labels in `frontend/src/components/CitationList.tsx` and `frontend/src/components/EscalationCard.tsx`.
- [ ] T048 [US3] Add linked-page, attached-document, form, portal, and office-contact cases to `backend/fixtures/evaluation_resources.json`.

**Checkpoint**: User Stories 1-3 provide either a supported answer with its exact resource or a safe escalation.

---

## Phase 6: User Story 4 - Ask Follow-up Questions in Context (Priority: P3)

**Goal**: Preserve short-lived anonymous topic, campus, term, program, course, and source context for safe follow-up questions.

**Independent Test**: Ask a supported initial question, then a related follow-up; verify that retained context is applied, is not exposed in response fields, expires after TTL, and triggers clarification when ambiguity remains.

### Tests for User Story 4

- [ ] T049 [P] [US4] Add conversation-context unit and integration tests for context creation, accepted updates, TTL expiry, ambiguity, and source preservation in `backend/tests/integration/test_conversation_context.py`.
- [ ] T050 [P] [US4] Add browser tests for a contextual follow-up and a follow-up requiring clarification in `tests/e2e/follow_up_context.spec.ts`.

### Implementation for User Story 4

- [ ] T051 [US4] Implement opaque anonymous conversation state with topic, campus, term, program, course, source IDs, timestamps, and TTL cleanup in `backend/src/services/conversation_context.py`; do not store raw transcripts, account identifiers, raw IP addresses, or user-agent data.
- [ ] T052 [US4] Integrate conversation context into question analysis and retrieval in `backend/src/services/question_analysis.py` and `backend/src/api/chat.py`, preserving accepted context while returning only the opaque conversation ID and topic.
- [ ] T053 [US4] Add conversation ID handling, follow-up loading state, and context-preserving message behavior in `frontend/src/services/chatApi.ts` and `frontend/src/components/ChatWidget.tsx`.
- [ ] T054 [US4] Add context-preservation, ambiguity, expiry, and cross-topic safety cases to `backend/fixtures/evaluation_followups.json`.

**Checkpoint**: All four user stories are independently testable, with follow-up context bounded by TTL and governance rules.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate pilot-wide quality, deployment readiness, performance, and governance.

- [ ] T055 [P] Add the fixed evaluation runner for at least 100 supported questions plus negative, stale, conflicting, personalized, campus-ambiguous, and out-of-scope cases in `backend/src/evaluation/runner.py` and `backend/fixtures/evaluation_manifest.json`.
- [ ] T056 [P] Add Playwright coverage for allowlisted-origin embedding, rejected origins, mobile layout, citation navigation, rate limits, and response states in `tests/e2e/widget.spec.ts`.
- [ ] T057 [P] Add filtered HNSW benchmark reporting against exact pgvector retrieval in `backend/src/evaluation/retrieval_benchmark.py`; do not enable approximate retrieval unless filtered recall is demonstrated.
- [ ] T058 Configure Docker health checks, persistent PostgreSQL volume, migrations-on-startup, HTTPS deployment settings, non-root containers, and operational limits in `docker-compose.yml`, `backend/Dockerfile`, and `README.md`.
- [ ] T059 Add latency, citation correctness, safe-refusal rate, context preservation, and source review metrics dashboards or export in `backend/src/metrics/` and `backend/src/evaluation/report.py`.
- [ ] T060 Run the complete validation procedure from `specs/001-pnw-student-information-chatbot/quickstart.md` and record results for SC-001 through SC-007 in `specs/001-pnw-student-information-chatbot/validation-results.md`.
- [ ] T061 Update `specs/001-pnw-student-information-chatbot/contracts/chat-api.md` and `specs/001-pnw-student-information-chatbot/data-model.md` for any implementation-level contract or schema differences found during validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001-T006 can start immediately; T001 is required before backend tasks and T002 before frontend tasks.
- **Foundational (Phase 2)**: T007-T021 depend on the relevant setup tasks and block all user stories.
- **User Story 1 (Phase 3)**: T022-T032 depend on the foundational phase and is the MVP increment.
- **User Story 2 (Phase 4)**: T033-T041 depends on the foundational phase and the answer/response contracts from User Story 1; safety services can be developed in parallel with late US1 work.
- **User Story 3 (Phase 5)**: T042-T048 depends on source and citation infrastructure from the foundational phase and User Story 1 grounding output.
- **User Story 4 (Phase 6)**: T049-T054 depends on the chat endpoint from User Story 1 and safety behavior from User Story 2.
- **Polish (Phase 7)**: T055-T061 depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational; no dependency on later stories.
- **US2 (P1)**: Depends on Foundational and the response-state contract from US1; its safety policy remains independently testable.
- **US3 (P2)**: Depends on Foundational and US1 citation assembly; it extends rather than replaces answer behavior.
- **US4 (P3)**: Depends on US1 chat handling and US2 ambiguity/refusal behavior.

### Parallel Opportunities

- T002-T006 can run in parallel after the project structure is agreed.
- T008-T009, T012-T014, and T019-T020 can run in parallel once the backend skeleton exists.
- T022-T024, T033-T035, T042-T043, and T049-T050 are parallel test tasks within their stories.
- After Foundational completes, US1 and the non-endpoint portions of US2 can proceed in parallel.
- US3 resource extraction and US4 conversation-context implementation can proceed in parallel once their US1 contracts are stable.
- T055-T059 are parallel polish tasks after the story implementations stabilize.

## Parallel Example: User Story 1

```text
Task: "Add POST /api/chat contract tests in backend/tests/contract/test_chat_api.py"
Task: "Add grounded-answer integration tests in backend/tests/integration/test_grounded_answers.py"
Task: "Add React widget tests in frontend/tests/chat-widget.test.tsx"
```

## Parallel Example: RAG Preparation

```text
Task: "Implement deterministic chunking in backend/src/services/chunking.py"
Task: "Implement configurable embeddings in backend/src/services/embeddings.py"
Task: "Implement ingestion validation reports in backend/src/services/ingestion_validation.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 Setup.
2. Complete Phase 2 Foundational, including the source ingestion workflow and governed retrieval.
3. Complete Phase 3 User Story 1.
4. Run the independent US1 test set and the supported-question evaluation.
5. Deploy or demo only after citations, source eligibility, and latency checks pass.

### Incremental Delivery

1. Add US2 safe refusal and escalation handling, then validate unsupported and conflicting cases.
2. Add US3 exact resource discovery and office destinations, then validate linked resources.
3. Add US4 short-lived follow-up context, then validate ambiguity and TTL behavior.
4. Complete cross-cutting evaluation, deployment, performance, and documentation tasks.

## Notes

- Every task is a checkbox with a sequential ID; `[P]` marks tasks that can run in parallel, and story phases use `[US1]` through `[US4]` labels.
- Backend models must preserve source provenance, review dates, content hashes, embedding configuration, and citation locators.
- The pilot does not authenticate users, access student systems, or add a student feedback workflow.
- Tests are included because the specification defines independent tests, acceptance scenarios, measurable success criteria, and a fixed evaluation set.
