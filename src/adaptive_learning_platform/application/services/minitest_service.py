from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class MinitestError(Exception):
    pass


class ArticleNotAssigned(MinitestError):
    pass


class NotRequiredArticle(MinitestError):
    pass


class MinitestNotConfigured(MinitestError):
    pass


@dataclass(frozen=True)
class OptionDTO:
    id: int
    pos: int
    text: str


@dataclass(frozen=True)
class QuestionDTO:
    id: int
    text: str
    options: List[OptionDTO]


@dataclass(frozen=True)
class GetMinitestResult:
    article_id: int
    questions: List[QuestionDTO]


@dataclass(frozen=True)
class SubmitMinitestResult:
    article_id: int
    passed: bool
    correct_cnt: int
    total_cnt: int = 3


def _get_active_stage_id(db: Session, user_id: int) -> int:
    row = db.execute(
        text("SELECT stage_id FROM user_stage_progress WHERE user_id=:uid AND status='active' LIMIT 1"),
        {"uid": user_id},
    ).fetchone()
    if row is None:
        raise MinitestError("У пользователя нет активной стадии")
    return int(row[0])


def get_minitest(db: Session, *, user_id: int, article_id: int) -> GetMinitestResult:
    stage_id = _get_active_stage_id(db, user_id)

    # проверяем назначение и тип
    row = db.execute(
        text(
            """
            SELECT kind, minitest_passed
            FROM user_stage_articles
            WHERE user_id=:uid AND stage_id=:sid AND article_id=:aid
            """
        ),
        {"uid": user_id, "sid": stage_id, "aid": article_id},
    ).fetchone()
    if row is None:
        raise ArticleNotAssigned("Статья не назначена пользователю на текущей стадии")

    kind = str(row[0])
    if kind != "required":
        raise NotRequiredArticle("Мини-тест доступен только для required статей")

    # берём 3 вопроса мини-теста
    qrows = db.execute(
        text(
            """
            SELECT q.id, q.text, ao.id, ao.pos, ao.text
            FROM article_minitest_questions amq
            JOIN questions q ON q.id = amq.question_id
            JOIN answer_options ao ON ao.question_id = q.id
            WHERE amq.article_id = :aid
            ORDER BY amq.pos, ao.pos
            """
        ),
        {"aid": article_id},
    ).fetchall()

    if not qrows:
        raise MinitestNotConfigured("Для статьи не настроены вопросы мини-теста")

    by_q: Dict[int, Dict[str, Any]] = {}
    for qid, qtext, oid, opos, otext in qrows:
        qid = int(qid)
        if qid not in by_q:
            by_q[qid] = {"id": qid, "text": str(qtext), "options": []}
        by_q[qid]["options"].append(OptionDTO(id=int(oid), pos=int(opos), text=str(otext)))

    questions = [QuestionDTO(id=v["id"], text=v["text"], options=v["options"]) for v in by_q.values()]
    return GetMinitestResult(article_id=article_id, questions=questions)


def submit_minitest(db: Session, *, user_id: int, article_id: int, answers: List[dict]) -> SubmitMinitestResult:
    stage_id = _get_active_stage_id(db, user_id)

    row = db.execute(
        text(
            """
            SELECT kind, minitest_passed
            FROM user_stage_articles
            WHERE user_id=:uid AND stage_id=:sid AND article_id=:aid
            FOR UPDATE
            """
        ),
        {"uid": user_id, "sid": stage_id, "aid": article_id},
    ).fetchone()
    if row is None:
        raise ArticleNotAssigned("Статья не назначена пользователю на текущей стадии")

    kind = str(row[0])
    already_passed = bool(row[1])

    if kind != "required":
        raise NotRequiredArticle("Мини-тест доступен только для required статей")

    if already_passed:
        return SubmitMinitestResult(article_id=article_id, passed=True, correct_cnt=3)

    # список вопросов мини-теста (3)
    qids = db.execute(
        text("SELECT question_id FROM article_minitest_questions WHERE article_id=:aid ORDER BY pos"),
        {"aid": article_id},
    ).fetchall()
    if len(qids) != 3:
        raise MinitestNotConfigured("Мини-тест должен содержать ровно 3 вопроса")

    expected_qids = [int(r[0]) for r in qids]
    expected_set = set(expected_qids)

    if len(answers) != 3:
        raise MinitestError("Нужно отправить ответы ровно на 3 вопроса")

    seen: set[int] = set()
    for a in answers:
        qid = int(a["question_id"])
        if qid not in expected_set:
            raise MinitestError(f"Вопрос {qid} не входит в мини-тест статьи")
        if qid in seen:
            raise MinitestError(f"Дублирующийся ответ на вопрос {qid}")
        seen.add(qid)

    # считаем правильные ответы (без хранения истории мини-теста)
    correct_cnt = 0
    for a in answers:
        qid = int(a["question_id"])
        oid = int(a["selected_option_id"])
        ok = db.execute(
            text("SELECT 1 FROM questions WHERE id=:qid AND correct_option_id=:oid"),
            {"qid": qid, "oid": oid},
        ).fetchone()
        if ok is not None:
            correct_cnt += 1

    passed = correct_cnt == 3
    if passed:
        db.execute(
            text(
                """
                UPDATE user_stage_articles
                SET minitest_passed=true, minitest_passed_at=now()
                WHERE user_id=:uid AND stage_id=:sid AND article_id=:aid AND minitest_passed=false
                """
            ),
            {"uid": user_id, "sid": stage_id, "aid": article_id},
        )

    return SubmitMinitestResult(article_id=article_id, passed=passed, correct_cnt=correct_cnt)