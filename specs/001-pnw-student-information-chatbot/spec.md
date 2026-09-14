# Feature Specification: PNW Student Information Chatbot

**Feature Branch**: `001-pnw-student-information-chatbot`

**Created**: 2026-09-14

**Status**: Draft

**Input**: User description: Create a chatbot for Purdue University Northwest students that answers common university questions using approved, current university information and directs students to authoritative sources or offices when it cannot answer reliably.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get a Reliable Answer to a University Question (Priority: P1)

As a PNW student, I want to ask a question in plain language and receive a clear answer grounded in approved university information so that I do not have to search across multiple webpages.

**Why this priority**: Reliable answers to common student questions are the primary student and staff need. This provides value even before broader navigation and escalation capabilities are added.

**Independent Test**: Ask representative questions about parking tickets, registration, academic standing, grade appeals, financial aid deadlines, and graduation procedures, then verify that each supported answer is accurate, understandable, and linked to its approved source.

**Acceptance Scenarios**:

1. **Given** approved information directly answers a student's question, **When** the student asks the question, **Then** the chatbot provides a concise answer and identifies the relevant official source.
2. **Given** a question could apply differently to Hammond or Westville, **When** the student asks about it without identifying a campus, **Then** the chatbot asks which campus applies before giving campus-specific information.
3. **Given** a question concerns a deadline or other time-sensitive rule, **When** the student asks the question, **Then** the chatbot states the applicable term or date context and provides the official source for verification.

---

### User Story 2 - Know When Information Is Unavailable or Uncertain (Priority: P1)

As a student, I want the chatbot to acknowledge when it cannot provide a reliable answer and tell me who to contact so that I do not act on incorrect university policy information.

**Why this priority**: The Dean of Students Office identified incorrect policy information as the highest risk. Safe refusal and escalation are required for trustworthy use.

**Independent Test**: Ask questions with missing, conflicting, outdated, personalized, or unsupported information and verify that the chatbot does not invent an answer and instead explains the limitation and provides an appropriate next step.

**Acceptance Scenarios**:

1. **Given** no approved source reliably answers the question, **When** the student asks it, **Then** the chatbot says it cannot provide a reliable answer and directs the student to an appropriate university office or advisor.
2. **Given** approved sources conflict or appear outdated, **When** the chatbot detects the conflict, **Then** it does not select an unsupported answer and identifies the need for confirmation from the responsible office.
3. **Given** a student asks for a personalized decision about registration, graduation, academic standing, or course planning, **When** the chatbot lacks the student's official records or required context, **Then** it provides only general information and recommends the appropriate advisor or office.

---

### User Story 3 - Find the Right Official Resource (Priority: P2)

As a student, I want the chatbot to summarize relevant information and point me to the official page, document, form, or department so that I can complete the next step without navigating a chain of unrelated links.

**Why this priority**: Interviews showed that students often find only links, follow multiple redirects, or do not know which department to contact. Guided resource discovery reduces that burden.

**Independent Test**: Ask questions that require a form, linked page, PDF, student portal, or department contact and verify that the response includes the relevant next step and official destination.

**Acceptance Scenarios**:

1. **Given** the answer requires a form, portal, or linked document, **When** the student asks how to complete the process, **Then** the chatbot explains the known steps and provides the official destination.
2. **Given** the student asks which department or office can help, **When** the responsible office is known, **Then** the chatbot identifies that office and provides its official contact or service information.
3. **Given** the official resource contains relevant information in linked pages or attached documents, **When** the chatbot answers from that resource, **Then** it provides the specific source link that supports the answer rather than only the top-level page.

---

### User Story 4 - Ask Follow-up Questions in Context (Priority: P3)

As a student, I want to ask a follow-up question about the current topic so that I can clarify a process without restating all of the context.

**Why this priority**: Conversational follow-up improves usability, but the chatbot still provides value for independent one-question interactions.

**Independent Test**: Ask a supported initial question, then ask a related follow-up involving a date, campus, document, or next step and verify that the answer uses the prior context without changing the approved meaning.

**Acceptance Scenarios**:

1. **Given** the chatbot has answered a question about a process, **When** the student asks a related follow-up, **Then** the chatbot uses the prior topic and preserves the relevant campus, term, and source context.
2. **Given** a follow-up introduces an ambiguity that affects the answer, **When** the chatbot cannot safely infer the missing context, **Then** it asks a targeted clarification question before answering.

### Edge Cases

- A student asks about a future term for which no approved schedule or deadline has been published.
- A source page links to a PDF, form, portal, or nested page that is unavailable or cannot be verified.
- A deadline table contains multiple terms, campuses, programs, or event types that could be confused.
- A course or program appears under different colleges, catalogs, or campus tags.
- A student asks for an answer that depends on private academic, financial, or disciplinary records.
- The student provides an error message that is not documented in approved PNW information.
- The question is outside PNW university information, requests legal or medical advice, or asks the chatbot to make a decision on behalf of an office.
- Official sources contain conflicting statements or a source's effective date cannot be established.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chatbot MUST accept student questions in plain language about PNW policies, rules, deadlines, procedures, programs, courses, campus services, and responsible offices.
- **FR-002**: The chatbot MUST answer policy-related questions only from approved PNW information identified as authoritative for the topic.
- **FR-003**: Each answer that relies on official information MUST identify the supporting official page, document, form, or office.
- **FR-004**: The chatbot MUST present answers in clear language that summarizes the relevant action, requirement, date, or contact information without requiring the student to inspect multiple unrelated pages.
- **FR-005**: The chatbot MUST preserve the relationship between a deadline and its term, campus, program, event type, or other applicable context.
- **FR-006**: The chatbot MUST ask for missing context, including campus, term, student level, or program, when that context materially changes the answer.
- **FR-007**: The chatbot MUST distinguish general information from personalized academic, financial, registration, graduation, or disciplinary decisions.
- **FR-008**: The chatbot MUST state that it cannot provide a reliable answer when approved information is missing, conflicting, outdated, inaccessible, or insufficient.
- **FR-009**: When it cannot answer reliably, the chatbot MUST recommend an appropriate PNW office, advisor, or official service and provide available contact or source information.
- **FR-010**: The chatbot MUST NOT invent policies, deadlines, course requirements, program availability, contacts, or procedural steps.
- **FR-011**: The chatbot MUST support official information contained in webpages, linked pages, attached documents, PDFs, and structured tables without losing the meaning of headings, list items, table rows, dates, or campus labels.
- **FR-012**: The chatbot MUST provide the specific official source that supports an answer when the supporting information is located in a linked or attached resource.
- **FR-013**: The chatbot MUST support follow-up questions while retaining relevant conversation context, including the topic, campus, term, and source.
- **FR-014**: The chatbot MUST identify when a question is outside the supported PNW information scope and direct the student to an appropriate human resource.
- **FR-015**: The chatbot MUST make no changes to student records, registration, schedules, financial aid, grades, or other university systems as part of answering questions.
- **FR-016**: Maintainers MUST be able to identify the approved source and review date associated with information used for policy-related answers.

### Key Entities *(include if feature involves data)*

- **Approved Source**: An official PNW webpage, linked page, PDF, form, catalog entry, schedule, policy, or office resource authorized for student information.
- **Student Question**: A natural-language request, including optional campus, term, program, course, or process context.
- **Answer**: A plain-language response containing supported information, applicable context, source attribution, and, when needed, a limitation or escalation.
- **Source Review Record**: The approval status, source location, effective or publication date when available, and review date for an approved source.
- **Escalation Destination**: The PNW office, advisor, department, or official service that can resolve a question the chatbot cannot answer reliably.
- **Conversation Context**: Relevant prior topic, campus, term, program, course, and source information used to interpret follow-up questions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a representative evaluation set of at least 100 supported PNW questions, at least 95% of answers contain no unsupported policy, deadline, requirement, or contact claim.
- **SC-002**: For at least 90% of supported questions in the evaluation set, students can identify the requested answer or next action from the first response without opening more than one additional official source.
- **SC-003**: At least 90% of questions involving a deadline, campus, program, course, or term include the applicable context or ask for the missing context before answering.
- **SC-004**: For at least 95% of unsupported, conflicting, outdated, or personalized questions in the evaluation set, the chatbot clearly states its limitation and provides an appropriate escalation destination when one is known.
- **SC-005**: In usability evaluation, at least 80% of participating students report that the chatbot is easier to use than searching across multiple PNW webpages for the tested questions.
- **SC-006**: The Dean of Students Office reports a measurable reduction of at least 25% in repetitive inquiries covered by the chatbot during an agreed evaluation period.
- **SC-007**: Students receive an initial response to at least 95% of submitted questions within 5 seconds under expected pilot usage.

## Assumptions

- The initial release targets current and prospective PNW students seeking general university information; it does not authenticate users or access personal student records.
- The Dean of Students Office and designated PNW offices will identify which sources are approved and will review high-impact policy, deadline, and requirement information.
- The initial scope covers general information and guided escalation, not automated advising, degree auditing, schedule construction, registration changes, appeals decisions, or other actions on behalf of university staff.
- Campus-specific questions primarily concern Hammond and Westville; the chatbot asks for campus context when the source does not apply uniformly.
- Official source links and office contact details may change and require an ongoing review process.
- The initial supported corpus includes the PNW parking regulations and enforcement information, academic catalog and program information, registrar academic schedules, graduate school information, accessibility information, academic integrity policy, student handbook, classroom behavior policy, and information services policies, subject to approval and review.
- Source content may be delivered through nested webpages, linked documents, PDFs, expandable sections, and tables; the chatbot must preserve meaning regardless of that presentation.
