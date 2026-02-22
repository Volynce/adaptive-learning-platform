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