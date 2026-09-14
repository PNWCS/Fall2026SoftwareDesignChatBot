<!--
Sync Impact Report
- Version change: template/unversioned → 1.0.0
- Modified principles: none; replaced scaffold placeholders with three project principles
- Added sections: Information Integrity; Requirements and Human Review
- Removed sections: none
- Follow-up TODOs: confirm the original ratification date
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

### III. Requirements Before Implementation
Every feature MUST have clear, reviewable, and testable requirements before implementation
begins. Important ambiguities MUST be resolved by humans rather than silently decided by
AI. This makes scope and expected behavior explicit before engineering effort is committed.

## Information Integrity

Approved university sources MUST be identifiable for policy-related answers. Requirements,
designs, and acceptance criteria MUST distinguish authoritative facts from assumptions,
interpretations, and unresolved questions. When sources conflict or cannot be verified,
the conflict MUST be surfaced and the system MUST follow the Fail Safely principle.

## Requirements and Human Review

Feature work MUST include reviewable requirements and acceptance criteria before coding.
Human review is required for unresolved policy interpretation, material scope decisions,
and changes that could alter the system's handling of authoritative information. Reviews
MUST confirm compliance with this constitution and record any accepted limitations.

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

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): confirm original adoption date | **Last Amended**: 2026-09-14
