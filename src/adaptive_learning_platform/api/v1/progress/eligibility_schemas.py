from pydantic import BaseModel
from typing import List


class MissingArticleOut(BaseModel):
    article_id: int
    module_id: int
    module_name: str
    title: str
    kind: str  # required/optional


class EligibilityReportOut(BaseModel):
    user_id: int
    stage_id: int
    rank: str
    level: int
    settings_version_id: int
    required_total: int
    required_done: int
    optional_total: int
    optional_done: int
    missing_required: List[MissingArticleOut]
    missing_optional: List[MissingArticleOut]
    eligible: bool