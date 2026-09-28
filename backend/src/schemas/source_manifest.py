from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models.enums import Campus, SourceType

_TRACKING_PARAMETERS = {"fbclid", "gclid"}


def canonicalize_official_url(value: AnyHttpUrl | str) -> str:
    parsed = urlsplit(str(value))
    host = parsed.hostname
    if parsed.scheme.lower() != "https":
        raise ValueError("source URL must use HTTPS")
    if host is None or not (host == "pnw.edu" or host.endswith(".pnw.edu")):
        raise ValueError("source URL must use the official pnw.edu domain")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("source URL must not include credentials")
    if parsed.port not in (None, 443):
        raise ValueError("source URL must not specify a non-standard port")

    query = [
        (key, item)
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_PARAMETERS and not key.lower().startswith("utm_")
    ]
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit(("https", host.lower(), path, urlencode(sorted(query)), ""))


class ApplicabilityMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    campuses: list[Campus] = Field(default_factory=list)
    terms: list[str] = Field(default_factory=list)
    programs: list[str] = Field(default_factory=list)
    universal: bool = False

    @field_validator("campuses", mode="after")
    @classmethod
    def unique_campuses(cls, value: list[Campus]) -> list[Campus]:
        return list(dict.fromkeys(value))

    @field_validator("terms", "programs", mode="before")
    @classmethod
    def normalize_scope_values(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
            raise ValueError("scope values must be strings")
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def require_scope(self) -> "ApplicabilityMetadata":
        has_scope = bool(self.campuses or self.terms or self.programs)
        if self.universal == has_scope:
            raise ValueError("provide applicability values or set universal=true, but not both")
        return self


class SourceManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    url: AnyHttpUrl
    title: str = Field(min_length=1)
    owner_office: str = Field(min_length=1)
    source_type: SourceType
    applicability: ApplicabilityMetadata
    review_window_days: int = Field(gt=0)

    @field_validator("url")
    @classmethod
    def validate_official_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        canonicalize_official_url(value)
        return value

    @field_validator("title", "owner_office", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be blank")
        return normalized

    @property
    def canonical_url(self) -> str:
        return canonicalize_official_url(self.url)