from typing import List
from pydantic import BaseModel


class AssignContentResponse(BaseModel):
    stage_id: int
    diagnostika_id: int
    assigned_optional: int
    assigned_required: int
    weak_module_ids: List[int]


class AssignedArticleOut(BaseModel):
    article_id: int
    module_id: int
    module_name: str
    title: str
    content_ref: str
    kind: str
    is_read: bool
    minitest_passed: bool