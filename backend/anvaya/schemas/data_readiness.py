from pydantic import BaseModel, ConfigDict


class ImportFailureData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    row: int
    category: str
    reason: str


class ImportJobData(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    input_format: str
    mapped_fields: list[str]
    missing_required_keys: list[str]
    accepted_count: int
    failed_count: int
    failures: list[ImportFailureData]
    status: str
    import_timestamp: str
    checksum: str
    source_version: str
    committed_at: str | None = None
