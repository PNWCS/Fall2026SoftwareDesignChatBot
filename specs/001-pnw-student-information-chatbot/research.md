# Research: PNW Student Information Chatbot

## Decision 1: Use a governed FastAPI service with a React widget

- **Decision**: Separate the public React widget from a FastAPI backend with API, retrieval, grounding, source, and conversation services.
- **Rationale**: The backend can enforce approval, context, citation, privacy, and refusal rules independently of presentation. A structured API keeps answer, clarification, refusal, and error states testable.
- **Alternatives considered**: A single full-stack application would be quicker to start but would couple UI behavior to policy logic and make safety checks harder to test.

## Decision 2: Use PostgreSQL with pgvector for the pilot

- **Decision**: Store source governance records, content chunks, embeddings, conversations, and escalation destinations in PostgreSQL with the pgvector extension.
- **Rationale**: The fixed pilot corpus is small enough for exact vector search, while relational filters can enforce approval, active-source status, review validity, campus, term, and program applicability before generation.
- **Alternatives considered**: A dedicated vector database could scale independently but would split governance metadata from retrieval and add operational complexity before the pilot demonstrates demand.

## Decision 3: Use hybrid retrieval with conservative eligibility filters

- **Decision**: Combine PostgreSQL full-text/lexical matching with pgvector similarity. Start with exact vector search, benchmark filtered HNSW, and enable approximate indexing only when filtered recall is demonstrated.
- **Rationale**: Names, dates, office contacts, and campus labels benefit from lexical matching; semantic matching handles natural-language questions. Exact search avoids premature filtered-index recall loss for a small corpus.
- **Alternatives considered**: Vector-only retrieval can confuse similar deadlines across campuses or terms. Immediate HNSW can be faster but must be validated with the same metadata filters used in production.

## Decision 4: Make source eligibility a database and application invariant

- **Decision**: Only chunks linked to an approved, active source with a valid review window and applicable metadata may reach answer generation.
- **Rationale**: Prompt instructions cannot reliably prevent stale or unapproved material from being used. SQL filters and a second grounding validator make the constitution's Grounded Answers and Fail Safely principles executable.
- **Alternatives considered**: Retrieving broadly and filtering after model generation risks exposing unsupported material and makes auditability weaker.

## Decision 5: Use structured model output and backend-built citations

- **Decision**: The model receives delimited excerpts and must return a structured answer state plus cited chunk IDs. The backend validates the state, evidence threshold, required context, and citation IDs, then constructs title, URL, page/section, and review metadata from stored records.
- **Rationale**: The model must not invent URLs, sources, or policy claims. Backend validation supports deterministic refusal and clarification behavior.
- **Alternatives considered**: Free-form model responses with prompt-only citations are less reliable and difficult to contract-test.

## Decision 6: Preserve only short-lived anonymous context

- **Decision**: Use an opaque anonymous conversation ID and store only normalized topic, campus, term, program, source IDs, and timestamps with a short TTL. Do not authenticate users or access student systems.
- **Rationale**: Follow-up questions need context, but the pilot must minimize FERPA and privacy exposure. Raw transcripts and likely personal data should not be retained for routine operation.
- **Alternatives considered**: Client-only history minimizes server retention but cannot consistently apply context to retrieval; full transcript retention creates unnecessary privacy and breach risk.

## Decision 7: Deploy with Docker Compose for the pilot

- **Decision**: Run separate containers for the React static server, FastAPI service, and PostgreSQL/pgvector, with migrations, health checks, a persistent database volume, and external TLS termination.
- **Rationale**: This satisfies the Docker deployment requirement while keeping the pilot operationally understandable and independently testable.
- **Alternatives considered**: Kubernetes would add operational overhead before campus-wide scale is established; one container would reduce isolation and make independent upgrades harder.

## Decision 8: Apply public-endpoint controls

- **Decision**: Restrict CORS to official PNW origins, require HTTPS at deployment, cap request size, rate-limit anonymous conversations, set model and database timeouts, and run application containers as non-root users.
- **Rationale**: A public anonymous endpoint can be scripted, abused, or used to generate unexpected model costs. These controls protect availability and reduce privacy risk.
- **Alternatives considered**: Wildcard CORS and unrestricted requests are simpler but inappropriate for an official public service.

## Operational clarification

The spec combines a fixed approved corpus with no mandatory human review before a new source is used. The implementation interprets this as follows: only entries marked `approved` in the corpus can answer students; ingestion may be automated, but unapproved entries remain ineligible; scheduled review can mark entries expired, blocked, or archived. When effective dates are unavailable, the source remains eligible only while its explicit review window is valid.
