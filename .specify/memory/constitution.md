<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles: III. Requirements Before Implementation → III. Source Provenance and Review
- Added sections: none
- Removed sections: none
- Follow-up TODOs: confirm original ratification date
-->

# University Information Assistant Constitution

## Core Principles

### I. Grounded Answers
All answers about university policies, rules, deadlines, and procedures MUST be grounded
in approved university information. The system MUST NOT present unsupported information as
official university policy. This protects users from relying on inaccurate or unofficial
guidance.

### II. Fail Safely
When reliable information is insufficient, the system MUST clearly state that it cannot
provide a reliable answer. It MUST prefer saying that it does not know or directing the
user to an appropriate university office over generating an unsupported answer. This
prevents false confidence and provides a safe path to authoritative help.

### III. Source Provenance and Review
Every source added to the approved corpus MUST be traceable to an official university
document, webpage, or office record. If a document is ingested, it is treated as reviewed
by a human for the purposes of this pilot, and no separate mandatory human-review gate
is required before the source may be used in official answers. This preserves source
accountability without creating duplicate review steps for accepted material.

## Information Integrity

Approved university sources MUST be identifiable for policy-related answers. Requirements,
designs, and acceptance criteria MUST distinguish authoritative facts from assumptions,
interpretations, and unresolved questions. When sources conflict or cannot be verified,
the conflict MUST be surfaced and the system MUST follow the Fail Safely principle.

## Requirements and Human Review

Feature work MUST include reviewable requirements and acceptance criteria before coding.
For ingested documents, explicit human review is not a separate mandatory gate: ingestion
itself is the approval action when the source is added to the approved corpus and its
provenance is recorded. A later dispute, conflict, or source quality issue still requires
the system to escalate, document the issue, and reclassify or remove the source as needed.

## Governance

This constitution governs project behavior and takes precedence over conflicting informal
practices. Amendments require a documented rationale, an explicit version change, and
review by project maintainers. A change that adds a principle or materially expands
governance increments the minor version; a backward-incompatible removal or redefinition
increments the major version; clarifications and non-semantic corrections increment the
patch version.

Every feature specification, implementation plan, code review, and release review MUST
consider compliance with the principles above. Non-compliance MUST be corrected before
release or explicitly recorded as a maintainer-approved exception with mitigation.

**Version**: 1.1.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-09-16
