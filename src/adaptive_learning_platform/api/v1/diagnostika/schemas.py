from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class AnswerOptionOut(BaseModel):
    id: int
    pos: int
    text: str


class QuestionOut(BaseModel):
    id: int
    text: str
    options: List[AnswerOptionOut]


class StartDiagnostikaResponse(BaseModel):
    diagnostika_id: int
    total_q: int
    questions: List[QuestionOut]


class SubmitAnswerIn(BaseModel):
    question_id: int
    selected_option_id: int


class SubmitDiagnostikaRequest(BaseModel):
    diagnostika_id: int
    answers: List[SubmitAnswerIn] = Field(min_length=1)


class ModuleStatOut(BaseModel):
    module_id: int
    correct_cnt: int
    total_cnt: int


class SubmitDiagnostikaResponse(BaseModel):
    diagnostika_id: int
    total_q: int
    score_total: int
    module_stats: List[ModuleStatOut]