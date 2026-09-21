# Data Model: PNW Student Information Chatbot

## ApprovedSource

Represents the canonical identity and ownership of an official PNW resource.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| canonical_url | text | Required; unique after canonicalization |
| title | text | Required |
| source_type | enum | webpage, linked_page, pdf, form, catalog, schedule, policy, office_resource |
| owner_office | text | Required for policy sources when known |
| status | enum | active, blocked, archived |
| created_at | timestamp | Required |
| updated_at | timestamp | Required |

Relationships: one source can have many `SourceChunk` records and one or more `EscalationDestination` associations.

## SourceChunk

A minimal excerpt used for retrieval and citation.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | Foreign key to ApprovedSource |
| ordinal | integer | Unique within source |
| content | text | Required |
| embedding | vector | pgvector embedding |
| search_document | tsvector | Lexical search representation |

A chunk stores the excerpt and retrieval metadata required to preserve meaning and filter results safely.

| heading_path | text | Section or table heading path; nullable for unstructured content |
| locator | text | PDF page, table identifier, or section locator; required for citations when available |
| campus | enum | Nullable applicability filter |
| term | text | Nullable applicability filter |
| program | text | Nullable applicability filter |
| effective_from | date | Nullable |
| effective_to | date | Nullable |

The chunk references a `SourceVersion`, which records the exact content and embedding configuration used to create it.

## SourceVersion

Represents one immutable fetched and processed revision of an approved source.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| source_id | UUID | Foreign key to ApprovedSource |
| content_hash | text | Required; unique per source and content |
| fetched_at | timestamp | Required |
| extraction_status | enum | pending, complete, failed |
| activation_status | enum | inactive, active, superseded, rejected |
| embedding_model | text | Required when embeddings are generated |
| embedding_dimension | integer | Required; must match database vector dimension |
| chunking_version | text | Required; identifies deterministic chunking rules |
| review_due_at | timestamp | Required for answer eligibility |
| activated_at | timestamp | Nullable |

Relationships: one source version has many `SourceChunk` records and one or more `IngestionJob` records. At most one current version for a source may be active.

## IngestionJob

Tracks each retryable preparation run and its validation evidence.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| source_version_id | UUID | Foreign key to SourceVersion |
| status | enum | pending, fetching, extracting, embedding, validating, complete, failed |
| dry_run | boolean | Required |
| chunk_count | integer | Required after extraction |
| embedded_count | integer | Required after embedding |
| validation_report | JSON | Required before activation; records checks and representative queries |
| error_code | text | Nullable structured failure reason |
| started_at | timestamp | Required |
| finished_at | timestamp | Nullable |

Required preparation checks are non-empty extraction, source hash consistency, complete chunk coverage, metadata validity, embedding dimension match, duplicate detection, and representative retrieval coverage. A failed job cannot activate its source version.

## StudentQuestion

An inbound anonymous request; store minimized data.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| message_redacted | text | Required; redact likely personal data before persistence/logging |
| created_at | timestamp | Required |

Do not store authentication identifiers, student records, raw IP addresses, or user-agent data unless a separately approved operational need exists.

Session memory holds the short-lived conversation history and context for follow-up interpretation; it is not persisted as a relational table in v1.

## Answer

The validated response returned to the widget.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| question_id | UUID | Foreign key to StudentQuestion |
| response_state | enum | answer, clarification, refusal, error |
| text | text | Required |
| escalation_destination_id | UUID | Nullable foreign key |
| latency_ms | integer | Required for performance evaluation |
| created_at | timestamp | Required |

An `answer` requires at least one valid citation and all claims must be supported by eligible chunks. A `clarification` must name the missing context. A `refusal` must state the limitation and provide an escalation destination when known.

## Citation

Backend-generated evidence attached to an answer.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| answer_id | UUID | Foreign key to Answer |
| source_chunk_id | UUID | Foreign key to SourceChunk |
| display_title | text | Copied from source metadata |
| url | text | Copied from canonical source or verified linked resource |
| locator | text | Section, heading, or PDF page when available |
| review_context | text | Effective/review date information |

The client never accepts arbitrary model-provided URLs as citations.

## EscalationDestination

An official office, advisor, department, or service for unresolved questions.

| Field | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| office_name | text | Required |
| service_description | text | Required |
| contact_url | text | Required and verified |
| phone | text | Nullable |
| email | text | Nullable |
| campus | enum | Nullable |
| active | boolean | Required |
| review_due_at | timestamp | Required |

## State transitions

- `ApprovedSource`: `active -> blocked`, `active -> archived`; answer eligibility requires the source to remain active and approved for the pilot corpus.
- `SourceVersion`: `inactive -> active -> superseded`; failed validation becomes `rejected`; only one current version per source may be answer-eligible.
- `IngestionJob`: `pending -> fetching -> extracting -> embedding -> validating -> complete`, or any stage -> `failed`; failed extraction or embedding is never answer-eligible.
- `Answer`: generated internally, then returned only after grounding validation. Invalid model output becomes `error` or `refusal`, never an unvalidated answer.
- `Session memory`: short-lived in-memory conversation state is created on first question, updated on accepted context, and discarded after TTL.
