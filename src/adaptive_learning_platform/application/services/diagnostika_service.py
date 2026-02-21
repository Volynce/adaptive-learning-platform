from dataclasses import dataclass
from typing import List, Dict, Any
import random

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


class DiagnostikaError(Exception):
    pass


class DiagnostikaAlreadyExists(DiagnostikaError):
    """Диагностика уже была создана (уникальность diagnostika_results.user_id)."""


class NotTraineeStage(DiagnostikaError):
    """Диагностика разрешена только на Trainee_0."""


class NotEnoughQuestions(DiagnostikaError):
    """Недостаточно активных вопросов для генерации попытки."""


class AlreadySubmitted(DiagnostikaError):
    """Ответы уже были отправлены ранее."""


@dataclass(frozen=True)
class AnswerOptionDTO:
    id: int
    pos: int
    text: str


@dataclass(frozen=True)
class QuestionDTO:
    id: int
    text: str
    options: List[AnswerOptionDTO]


@dataclass(frozen=True)
class StartDiagnostikaResult:
    diagnostika_id: int
    total_q: int
    questions: List[QuestionDTO]


@dataclass(frozen=True)
class ModuleStatDTO:
    module_id: int
    correct_cnt: int
    total_cnt: int


@dataclass(frozen=True)
class SubmitDiagnostikaResult:
    diagnostika_id: int
    total_q: int
    score_total: int
    module_stats: List[ModuleStatDTO]


def _get_active_stage_and_settings(db: Session, user_id: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT
              usp.stage_id,
              usp.settings_version_id,
              s.rank,
              s.level,
              t.id as track_id
            FROM user_stage_progress usp
            JOIN stages s ON s.id = usp.stage_id
            JOIN tracks t ON t.id = s.track_id
            WHERE usp.user_id = :uid AND usp.status = 'active'
            LIMIT 1
            """
        ),
        {"uid": user_id},
    ).fetchone()

    if row is None:
        raise NotTraineeStage("У пользователя нет активной стадии")

    stage_id = int(row[0])
    settings_version_id = int(row[1])
    rank = str(row[2])
    level = int(row[3])
    track_id = int(row[4])

    return {
        "stage_id": stage_id,
        "settings_version_id": settings_version_id,
        "rank": rank,
        "level": level,
        "track_id": track_id,
    }


def start_diagnostika(db: Session, *, user_id: int) -> StartDiagnostikaResult:
    # 1) Проверяем активную стадию
    ctx = _get_active_stage_and_settings(db, user_id)
    if not (ctx["rank"] == "trainee" and ctx["level"] == 0):
        raise NotTraineeStage("Диагностика разрешена только на Trainee_0")

    stage_id = ctx["stage_id"]
    settings_version_id = ctx["settings_version_id"]
    track_id = ctx["track_id"]

    # 2) Берём настройки диагностики
    srow = db.execute(
        text(
            """
            SELECT entry_total_q, entry_per_module_q
            FROM track_settings
            WHERE settings_version_id = :sv
            """
        ),
        {"sv": settings_version_id},
    ).fetchone()
    if srow is None:
        raise DiagnostikaError("Отсутствуют track_settings для активной версии настроек")

    entry_total_q = int(srow[0])
    entry_per_module_q = int(srow[1])

    # 3) Создаём diagnostika_results (один раз на пользователя)
    try:
        drow = db.execute(
            text(
                """
                INSERT INTO diagnostika_results(user_id, stage_id, total_q, score_total)
                VALUES (:uid, :sid, :tq, 0)
                RETURNING id
                """
            ),
            {"uid": user_id, "sid": stage_id, "tq": entry_total_q},
        ).fetchone()
    except IntegrityError as e:
        # уникальность diagnostika_results.user_id
        raise DiagnostikaAlreadyExists() from e

    diagnostika_id = int(drow[0])

    # 4) Загружаем список модулей и активных вопросов
    modules = db.execute(
        text("SELECT id FROM modules WHERE track_id = :tid ORDER BY id"),
        {"tid": track_id},
    ).fetchall()
    module_ids = [int(r[0]) for r in modules]

    qrows = db.execute(
        text(
            """
            SELECT q.id, q.module_id
            FROM questions q
            JOIN modules m ON m.id = q.module_id
            WHERE m.track_id = :tid AND q.is_active = true
            """
        ),
        {"tid": track_id},
    ).fetchall()

    pool_by_module: Dict[int, List[int]] = {mid: [] for mid in module_ids}
    for qid, mid in qrows:
        mid = int(mid)
        if mid in pool_by_module:
            pool_by_module[mid].append(int(qid))

    # 5) Выбор вопросов: per_module + добор до total
    selected: List[int] = []
    rng = random.Random()

    for mid in module_ids:
        pool = pool_by_module.get(mid, [])
        if pool:
            take = min(entry_per_module_q, len(pool))
            selected.extend(rng.sample(pool, k=take))

    # добор из всех оставшихся
    selected_set = set(selected)
    remaining_needed = entry_total_q - len(selected_set)

    all_pool = [qid for qid, _mid in [(int(r[0]), int(r[1])) for r in qrows] if qid not in selected_set]
    if remaining_needed > 0:
        if len(all_pool) < remaining_needed:
            raise NotEnoughQuestions(f"Недостаточно активных вопросов: нужно {entry_total_q}, доступно {len(selected_set)+len(all_pool)}")
        selected.extend(rng.sample(all_pool, k=remaining_needed))

    # финальная нормализация
    selected = list(dict.fromkeys(selected))  # убрать возможные дубли, сохранить порядок
    if len(selected) < entry_total_q:
        raise NotEnoughQuestions("Недостаточно вопросов после отбора")

    selected = selected[:entry_total_q]

    # 6) Запись diagnostika_attempt_questions
    for qid in selected:
        db.execute(
            text(
                "INSERT INTO diagnostika_attempt_questions(diagnostika_id, question_id) VALUES (:did, :qid)"
            ),
            {"did": diagnostika_id, "qid": qid},
        )

    # 7) Возврат payload вопросов с вариантами
    rows = db.execute(
        text(
            """
            SELECT
              q.id as qid, q.text as qtext,
              ao.id as oid, ao.pos as opos, ao.text as otext
            FROM diagnostika_attempt_questions dq
            JOIN questions q ON q.id = dq.question_id
            JOIN answer_options ao ON ao.question_id = q.id
            WHERE dq.diagnostika_id = :did
            ORDER BY q.id, ao.pos
            """
        ),
        {"did": diagnostika_id},
    ).fetchall()

    by_q: Dict[int, Dict[str, Any]] = {}
    for qid, qtext, oid, opos, otext in rows:
        qid = int(qid)
        if qid not in by_q:
            by_q[qid] = {"id": qid, "text": str(qtext), "options": []}
        by_q[qid]["options"].append(AnswerOptionDTO(id=int(oid), pos=int(opos), text=str(otext)))

    questions = [QuestionDTO(id=v["id"], text=v["text"], options=v["options"]) for v in by_q.values()]

    return StartDiagnostikaResult(diagnostika_id=diagnostika_id, total_q=entry_total_q, questions=questions)


def submit_diagnostika(db: Session, *, user_id: int, diagnostika_id: int, answers: List[dict]) -> SubmitDiagnostikaResult:
    # 1) Проверка принадлежности diagnostika пользователю + total_q
    own = db.execute(
        text("SELECT user_id, total_q FROM diagnostika_results WHERE id = :did"),
        {"did": diagnostika_id},
    ).fetchone()
    if own is None:
        raise DiagnostikaError("diagnostika_id не найден")
    if int(own[0]) != user_id:
        raise DiagnostikaError("Нет доступа к diagnostika_id")
    total_q = int(own[1])

    # 2) Запрет повторной отправки (любая запись ответов = submit уже был)
    already = db.execute(
        text("SELECT 1 FROM diagnostika_attempt_answers WHERE diagnostika_id = :did LIMIT 1"),
        {"did": diagnostika_id},
    ).fetchone()
    if already is not None:
        raise AlreadySubmitted()

    # 3) Загружаем полный список вопросов попытки (истина для submit)
    qrows = db.execute(
        text(
            """
            SELECT dq.question_id
            FROM diagnostika_attempt_questions dq
            WHERE dq.diagnostika_id = :did
            ORDER BY dq.question_id
            """
        ),
        {"did": diagnostika_id},
    ).fetchall()

    if not qrows:
        raise DiagnostikaError("Для diagnostika_id отсутствует набор вопросов (attempt_questions)")

    attempt_qids = [int(r[0]) for r in qrows]
    attempt_set = set(attempt_qids)

    # 4) Валидация: должны ответить на ВСЕ вопросы попытки
    if len(answers) != len(attempt_set):
        raise DiagnostikaError(f"Нужно отправить ответы на все вопросы: ожидается {len(attempt_set)}, получено {len(answers)}")

    seen: set[int] = set()
    for a in answers:
        qid = int(a["question_id"])
        if qid not in attempt_set:
            raise DiagnostikaError(f"Вопрос {qid} не входит в попытку diagnostika_id={diagnostika_id}")
        if qid in seen:
            raise DiagnostikaError(f"Дублирующийся ответ на вопрос {qid}")
        seen.add(qid)

    # 5) Вставка ответов (FK гарантирует принадлежность option выбранному question)
    for a in answers:
        db.execute(
            text(
                """
                INSERT INTO diagnostika_attempt_answers(diagnostika_id, question_id, selected_option_id)
                VALUES (:did, :qid, :oid)
                """
            ),
            {"did": diagnostika_id, "qid": int(a["question_id"]), "oid": int(a["selected_option_id"])},
        )

    # 6) Подсчёт score_total по ВСЕМ вопросам попытки (не по присланным)
    score_row = db.execute(
        text(
            """
            SELECT COALESCE(
              SUM(CASE WHEN a.selected_option_id = q.correct_option_id THEN 1 ELSE 0 END),
              0
            )::int AS score_total
            FROM diagnostika_attempt_questions dq
            JOIN questions q ON q.id = dq.question_id
            LEFT JOIN diagnostika_attempt_answers a
              ON a.diagnostika_id = dq.diagnostika_id AND a.question_id = dq.question_id
            WHERE dq.diagnostika_id = :did
            """
        ),
        {"did": diagnostika_id},
    ).fetchone()
    score_total = int(score_row[0])

    db.execute(
        text("UPDATE diagnostika_results SET score_total = :sc WHERE id = :did"),
        {"sc": score_total, "did": diagnostika_id},
    )

    # 7) Статистика по модулям также по ВСЕМ вопросам попытки
    db.execute(
        text(
            """
            INSERT INTO diagnostika_module_stats(diagnostika_id, module_id, correct_cnt, total_cnt)
            SELECT
              :did as diagnostika_id,
              q.module_id,
              COALESCE(SUM(CASE WHEN a.selected_option_id = q.correct_option_id THEN 1 ELSE 0 END), 0)::int as correct_cnt,
              COUNT(*)::int as total_cnt
            FROM diagnostika_attempt_questions dq
            JOIN questions q ON q.id = dq.question_id
            LEFT JOIN diagnostika_attempt_answers a
              ON a.diagnostika_id = dq.diagnostika_id AND a.question_id = dq.question_id
            WHERE dq.diagnostika_id = :did
            GROUP BY q.module_id
            """
        ),
        {"did": diagnostika_id},
    )

    mrows = db.execute(
        text(
            """
            SELECT module_id, correct_cnt, total_cnt
            FROM diagnostika_module_stats
            WHERE diagnostika_id = :did
            ORDER BY module_id
            """
        ),
        {"did": diagnostika_id},
    ).fetchall()

    module_stats = [ModuleStatDTO(module_id=int(r[0]), correct_cnt=int(r[1]), total_cnt=int(r[2])) for r in mrows]

    # total_q в diagnostika_results — нормативное (20), возвращаем его
    return SubmitDiagnostikaResult(
        diagnostika_id=diagnostika_id,
        total_q=total_q,
        score_total=score_total,
        module_stats=module_stats,
    )