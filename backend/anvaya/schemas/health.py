from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: Literal["anvaya-api"]
    environment: Literal["development", "testing", "production"]
    database: Literal["ok"]
    public_demo_enabled: bool = False
    ai_assist_enabled: bool = False
    voice_enabled: bool = False
