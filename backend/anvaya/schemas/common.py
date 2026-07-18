from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SuccessEnvelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=128)
    data: T
    warnings: list[str] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=128)
    code: str = Field(pattern=r"^[A-Z0-9_]+$")
    message: str
    retryable: bool
