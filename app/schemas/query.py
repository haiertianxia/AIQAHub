from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryFilters(BaseModel):
    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    search: str | None = None
    status: str | None = None
    project_id: str | None = None
    execution_id: str | None = None
    suite_id: str | None = None
    completion_source: str | None = None
    action: str | None = None
    target_type: str | None = None
    model_name: str | None = None
    insight_type: str | None = None
    sort: str | None = None

    @field_validator(
        "search",
        "status",
        "project_id",
        "execution_id",
        "suite_id",
        "completion_source",
        "action",
        "target_type",
        "model_name",
        "insight_type",
        "sort",
        mode="before",
    )
    @classmethod
    def strip_optional_strings(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value  # type: ignore[return-value]


class ListQueryParams(QueryFilters):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=200)


class ExportQueryParams(QueryFilters):
    pass
