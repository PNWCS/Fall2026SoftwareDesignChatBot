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

## Decision 9: Use Google Gemini through a backend-only provider boundary

- **Decision**: Call Google Gemini through the official `google-genai` Python client from the FastAPI backend. Select a free-tier-eligible Gemini model through configuration rather than hard-coding a model name in the API contract.
- **Rationale**: Gemini provides a practical hosted LLM option for the pilot while the backend boundary keeps the API key out of the browser and allows source filtering, structured-output validation, timeout handling, and provider replacement without changing the frontend contract. Free-tier quotas and model availability can change, so deployment configuration must remain adjustable.
- **Alternatives considered**: A paid-only hosted model could offer higher quotas but adds pilot cost; a locally hosted model avoids provider quotas but increases infrastructure and operations requirements; exposing the provider directly to the frontend would leak credentials and bypass grounding controls.

## Decision 10: Prepare the RAG store with versioned, idempotent ingestion

- **Decision**: Use a staged ingestion workflow that registers a source manifest, fetches and hashes the source, extracts structure-aware content, creates metadata-rich deterministic chunks, generates embeddings, loads lexical and vector representations transactionally, runs retrieval-quality checks, and activates the source version only after validation. Use the content hash plus source identity as the idempotency key, and retain superseded versions for audit without making them eligible for answers.
- **Rationale**: Embeddings are only useful when their source text, dimensions, applicability, and review state remain traceable. Versioned activation prevents partial loads, stale chunks, and changed content from silently altering historical answers. Hybrid lexical/vector retrieval preserves exact matches for dates, campus names, and office contacts while semantic search handles paraphrases.
- **Alternatives considered**: A one-off database seed is simpler but cannot reliably handle source updates, retries, partial failures, or review rollback. A managed vector store would provide retrieval infrastructure but would separate embeddings from the relational governance records required by the pilot.

## Decision 11: Use embedding and retrieval validation gates

- **Decision**: Store the embedding model name, dimension, chunking configuration, and ingestion job status with each source version. Reject dimension mismatches and incomplete extraction, and require representative retrieval queries to meet a configured recall/coverage threshold before activation. Start with exact pgvector search and benchmark filtered HNSW separately.
- **Rationale**: A successful database insert does not prove that a RAG corpus is usable or safe. Explicit validation catches malformed PDFs, lost table context, wrong embedding configuration, and metadata filters that hide required evidence before the model can answer.
- **Alternatives considered**: Trusting row counts or embedding API success would miss semantic retrieval failures; enabling HNSW immediately could make filtered recall harder to reason about for the small pilot corpus.

## Operational clarification

The spec combines a fixed approved corpus with no mandatory human review before a new source is used. The implementation interprets this as follows: only entries marked `approved` in the corpus can answer students; ingestion may be automated, but unapproved entries remain ineligible; scheduled review can mark entries expired, blocked, or archived. When effective dates are unavailable, the source remains eligible only while its explicit review window is valid.
