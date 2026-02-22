from pydantic import BaseModel
from typing import List


class AnswerOptionOut(BaseModel):
    id: int
    pos: int
    text: str


class ExamQuestionOut(BaseModel):
    id: int
    text: str
    options: List[AnswerOptionOut]


class StartLevelExamResponse(BaseModel):
    attempt_id: int
    attempt_no: int
    total_q: int
    questions: List[ExamQuestionOut]

class SubmitExamAnswerIn(BaseModel):
    question_id: int
    selected_option_id: int


class SubmitLevelExamRequest(BaseModel):
    answers: List[SubmitExamAnswerIn]

class ProgressActionOut(BaseModel):
    action: str
    from_stage_id: int
    to_stage_id: int | None = None

class SubmitLevelExamResponse(BaseModel):
    attempt_id: int
    score_total: int
    pass_score: int
    passed: bool
    progress: ProgressActionOut