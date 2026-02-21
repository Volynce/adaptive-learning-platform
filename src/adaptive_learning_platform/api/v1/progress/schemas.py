from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CurrentStageResponse(BaseModel):
    user_id: int
    track_id: int
    track_name: str

    stage_id: int
    rank: str = Field(description="trainee/junior/middle/senior")
    level: int = Field(description="0 для trainee, 1..3 для остальных")

    status: str
    activated_at: datetime
    settings_version_id: int