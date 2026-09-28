from enum import StrEnum


class Campus(StrEnum):
    HAMMOND = "hammond"
    WESTVILLE = "westville"


class SourceType(StrEnum):
    WEBPAGE = "webpage"
    LINKED_PAGE = "linked_page"
    PDF = "pdf"
    FORM = "form"
    CATALOG = "catalog"
    SCHEDULE = "schedule"
    POLICY = "policy"
    OFFICE_RESOURCE = "office_resource"


class SourceStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    ARCHIVED = "archived"


class ExtractionStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"


class SourceActivationStatus(StrEnum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class IngestionJobStatus(StrEnum):
    PENDING = "pending"
    FETCHING = "fetching"
    EXTRACTING = "extracting"
    EMBEDDING = "embedding"
    VALIDATING = "validating"
    COMPLETE = "complete"
    FAILED = "failed"


class ResponseState(StrEnum):
    ANSWER = "answer"
    CLARIFICATION = "clarification"
    REFUSAL = "refusal"
    ERROR = "error"
