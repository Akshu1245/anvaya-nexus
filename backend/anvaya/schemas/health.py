from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: Literal["anvaya-api"]
    environment: Literal["development", "testing", "production"]
    database: Literal["ok"]
