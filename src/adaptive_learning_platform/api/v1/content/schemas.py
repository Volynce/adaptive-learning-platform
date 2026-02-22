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

class AnswerOptionOut(BaseModel):
    id: int
    pos: int
    text: str

class MinitestQuestionOut(BaseModel):
    id: int
    text: str
    options: list[AnswerOptionOut]


class GetMinitestResponse(BaseModel):
    article_id: int
    questions: list[MinitestQuestionOut]


class SubmitMinitestAnswerIn(BaseModel):
    question_id: int
    selected_option_id: int


class SubmitMinitestRequest(BaseModel):
    answers: list[SubmitMinitestAnswerIn]


class SubmitMinitestResponse(BaseModel):
    article_id: int
    passed: bool
    correct_cnt: int
    total_cnt: int