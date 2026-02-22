from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from adaptive_learning_platform.application.services.eligibility_service import get_level_exam_eligibility, EligibilityReport

from datetime import datetime

from adaptive_learning_platform.application.services.progression_service import apply_progress_after_level_exam_pass, ProgressAction
class LevelExamError(Exception):
    pass


class NotEligible(LevelExamError):
    def __init__(self, report: EligibilityReport):
        super().__init__("Недопуск к level-exam")
        self.report = report


class AlreadyPassed(LevelExamError):
    pass


class NotEnoughQuestions(LevelExamError):
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
class StartLevelExamResult:
    attempt_id: int
    attempt_no: int
    total_q: int
    questions: List[QuestionDTO]


def _get_active_stage_ctx_for_update(db: Session, user_id: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT usp.stage_id, usp.settings_version_id, s.track_id, s.rank, s.level
            FROM user_stage_progress usp
            JOIN stages s ON s.id = usp.stage_id
            WHERE usp.user_id=:uid AND usp.status='active'
            FOR UPDATE
            """
        ),
        {"uid": user_id},
    ).fetchone()
    if row is None:
        raise LevelExamError("У пользователя нет активной стадии")
    return {
        "stage_id": int(row[0]),
        "settings_version_id": int(row[1]),
        "track_id": int(row[2]),
        "rank": str(row[3]),
        "level": int(row[4]),
    }


def start_level_exam(db: Session, *, user_id: int) -> StartLevelExamResult:
    # 1) сериализуем сценарий на строке прогресса (FOR UPDATE)
    ctx = _get_active_stage_ctx_for_update(db, user_id)
    stage_id = ctx["stage_id"]
    settings_version_id = ctx["settings_version_id"]

    # 2) eligibility (если false — возвращаем отчёт как основание отказа)
    rep = get_level_exam_eligibility(db, user_id=user_id)
    if not rep.eligible:
        raise NotEligible(rep)

    # 3) запрет пересдачи после PASS (инвариант также прикрыт partial unique)
    passed = db.execute(
        text(
            """
            SELECT 1
            FROM level_exam_attempts
            WHERE user_id=:uid AND stage_id=:sid AND passed=true
            LIMIT 1
            """
        ),
        {"uid": user_id, "sid": stage_id},
    ).fetchone()
    if passed is not None:
        raise AlreadyPassed("Level-exam уже сдан (PASS) для этой стадии")

    # 4) настройки экзамена
    srow = db.execute(
        text(
            """
            SELECT level_exam_total_q, k_exam, level_exam_min_per_module, level_exam_max_per_module
            FROM track_settings
            WHERE settings_version_id=:sv
            """
        ),
        {"sv": settings_version_id},
    ).fetchone()
    if srow is None:
        raise LevelExamError("Нет track_settings для активной версии настроек")
    total_q = int(srow[0])
    k_exam = int(srow[1])
    min_per = int(srow[2])
    max_per = int(srow[3])

    # 5) диагностические слабости (errors) → выбираем K слабых модулей
    drow = db.execute(text("SELECT id FROM diagnostika_results WHERE user_id=:uid LIMIT 1"), {"uid": user_id}).fetchone()
    if drow is None:
        raise LevelExamError("Нет diagnostika_results (ожидается для Trainee_0)")
    did = int(drow[0])

    weak_rows = db.execute(
        text(
            """
            SELECT module_id, (total_cnt - correct_cnt) AS errors
            FROM diagnostika_module_stats
            WHERE diagnostika_id=:did
            ORDER BY errors DESC, module_id ASC
            LIMIT :k
            """
        ),
        {"did": did, "k": k_exam},
    ).fetchall()
    weak = [{"module_id": int(r[0]), "errors": int(r[1])} for r in weak_rows]
    weak_ids = [w["module_id"] for w in weak]

    # 6) расклад квот: каждому weak module даём min_per, остаток распределяем по errors, ограничивая max_per
    alloc: Dict[int, int] = {mid: min_per for mid in weak_ids}
    remaining = total_q - (min_per * len(weak_ids))
    if remaining < 0:
        raise LevelExamError("Некорректные настройки: total_q меньше чем min_per_module * K_exam")

    # распределяем остаток по кругу, приоритет по errors
    while remaining > 0:
        progressed = False
        for w in sorted(weak, key=lambda x: (-x["errors"], x["module_id"])):
            mid = w["module_id"]
            if alloc[mid] < max_per and remaining > 0:
                alloc[mid] += 1
                remaining -= 1
                progressed = True
        if not progressed:
            # все достигли max_per, но ещё есть остаток → добиваем по любым модулям трека
            break

    # если ещё осталось — заполним из остальных модулей по 1 (чтобы total_q соблюсти)
    if remaining > 0:
        other_rows = db.execute(
            text("SELECT id FROM modules WHERE track_id=:tid AND id <> ALL(:weak_ids) ORDER BY id"),
            {"tid": ctx["track_id"], "weak_ids": weak_ids},
        ).fetchall()
        other_ids = [int(r[0]) for r in other_rows]
        if not other_ids:
            raise LevelExamError("Нет дополнительных модулей для добора вопросов")
        idx = 0
        while remaining > 0:
            mid = other_ids[idx % len(other_ids)]
            alloc[mid] = alloc.get(mid, 0) + 1
            remaining -= 1
            idx += 1

    # 7) выбираем вопросы по модулям (без дублей)
    selected_qids: List[int] = []
    for mid, need in alloc.items():
        cands = db.execute(
            text(
                """
                SELECT id
                FROM questions
                WHERE module_id=:mid AND is_active=true
                ORDER BY id
                """
            ),
            {"mid": mid},
        ).fetchall()
        cand_ids = [int(r[0]) for r in cands]
        if len(cand_ids) < need:
            raise NotEnoughQuestions(f"Недостаточно вопросов в module_id={mid}: нужно {need}, есть {len(cand_ids)}")
        selected_qids.extend(cand_ids[:need])

    # финальная проверка размера
    if len(selected_qids) != total_q:
        raise LevelExamError(f"Сборка вопросов дала {len(selected_qids)} вместо {total_q}")

    # 8) attempt_no
    an = db.execute(
        text("SELECT COALESCE(MAX(attempt_no),0)::int FROM level_exam_attempts WHERE user_id=:uid AND stage_id=:sid"),
        {"uid": user_id, "sid": stage_id},
    ).fetchone()
    attempt_no = int(an[0]) + 1

    # 9) создаём попытку
    arow = db.execute(
        text(
            """
            INSERT INTO level_exam_attempts(user_id, stage_id, attempt_no, score_total, passed)
            VALUES (:uid, :sid, :no, 0, false)
            RETURNING id
            """
        ),
        {"uid": user_id, "sid": stage_id, "no": attempt_no},
    ).fetchone()
    attempt_id = int(arow[0])

    # 10) фиксируем вопросы попытки
    for qid in selected_qids:
        db.execute(
            text("INSERT INTO level_exam_attempt_questions(attempt_id, question_id) VALUES (:aid, :qid)"),
            {"aid": attempt_id, "qid": qid},
        )

    # 11) возвращаем вопросы + варианты
    rows = db.execute(
        text(
            """
            SELECT q.id, q.text, ao.id, ao.pos, ao.text
            FROM level_exam_attempt_questions aq
            JOIN questions q ON q.id = aq.question_id
            JOIN answer_options ao ON ao.question_id = q.id
            WHERE aq.attempt_id=:aid
            ORDER BY q.id, ao.pos
            """
        ),
        {"aid": attempt_id},
    ).fetchall()

    by_q: Dict[int, Dict[str, Any]] = {}
    for qid, qtext, oid, opos, otext in rows:
        qid = int(qid)
        if qid not in by_q:
            by_q[qid] = {"id": qid, "text": str(qtext), "options": []}
        by_q[qid]["options"].append(OptionDTO(id=int(oid), pos=int(opos), text=str(otext)))

    questions = [QuestionDTO(id=v["id"], text=v["text"], options=v["options"]) for v in by_q.values()]
    return StartLevelExamResult(attempt_id=attempt_id, attempt_no=attempt_no, total_q=total_q, questions=questions)

@dataclass(frozen=True)
class SubmitLevelExamResult:
    attempt_id: int
    score_total: int
    pass_score: int
    passed: bool
    progress: ProgressAction


class AttemptNotFound(LevelExamError):
    pass


class AttemptAlreadyFinalized(LevelExamError):
    pass


class InvalidAnswers(LevelExamError):
    pass


def submit_level_exam(db: Session, *, user_id: int, attempt_id: int, answers: List[dict]) -> SubmitLevelExamResult:
    # 1) блокируем попытку на время проверки/записи
    row = db.execute(
        text(
            """
            SELECT a.id, a.user_id, a.stage_id, a.passed, usp.settings_version_id
            FROM level_exam_attempts a
            JOIN user_stage_progress usp ON usp.user_id=a.user_id AND usp.stage_id=a.stage_id
            WHERE a.id=:aid
            FOR UPDATE
            """
        ),
        {"aid": attempt_id},
    ).fetchone()

    if row is None:
        raise AttemptNotFound("Попытка level-exam не найдена")

    a_user_id = int(row[1])
    stage_id = int(row[2])
    passed = bool(row[3])
    settings_version_id = int(row[4])

    if a_user_id != user_id:
        raise AttemptNotFound("Попытка level-exam не принадлежит текущему пользователю")

    if passed:
        raise AttemptAlreadyFinalized("Попытка уже завершена PASS и не может быть пересдана/перезаписана")

    # 2) получаем вопросы попытки (20)
    qrows = db.execute(
        text("SELECT question_id FROM level_exam_attempt_questions WHERE attempt_id=:aid ORDER BY question_id"),
        {"aid": attempt_id},
    ).fetchall()
    qids = [int(r[0]) for r in qrows]
    if not qids:
        raise LevelExamError("У попытки нет закрепленных вопросов")

    expected_set = set(qids)

    if len(answers) != len(qids):
        raise InvalidAnswers(f"Нужно ответить на все вопросы попытки: {len(qids)} шт.")

    seen = set()
    for a in answers:
        qid = int(a["question_id"])
        if qid not in expected_set:
            raise InvalidAnswers(f"Вопрос {qid} не входит в попытку")
        if qid in seen:
            raise InvalidAnswers(f"Дублирующийся ответ на вопрос {qid}")
        seen.add(qid)

    # 3) pass_score из настроек
    srow = db.execute(
        text("SELECT level_exam_pass_score FROM track_settings WHERE settings_version_id=:sv"),
        {"sv": settings_version_id},
    ).fetchone()
    if srow is None:
        raise LevelExamError("Нет track_settings для активной версии настроек")
    pass_score = int(srow[0])

    # 4) очищаем предыдущие ответы (на случай повторного submit до PASS)
    db.execute(
        text("DELETE FROM level_exam_attempt_answers WHERE attempt_id=:aid"),
        {"aid": attempt_id},
    )

    # 5) вставляем ответы и считаем score
    score_total = 0
    for a in answers:
        qid = int(a["question_id"])
        oid = int(a["selected_option_id"])

        # FK (attempt_id,question_id) -> attempt_questions защитит от левых qid
        db.execute(
            text(
                """
                INSERT INTO level_exam_attempt_answers(attempt_id, question_id, selected_option_id)
                VALUES (:aid, :qid, :oid)
                """
            ),
            {"aid": attempt_id, "qid": qid, "oid": oid},
        )

        ok = db.execute(
            text("SELECT 1 FROM questions WHERE id=:qid AND correct_option_id=:oid"),
            {"qid": qid, "oid": oid},
        ).fetchone()
        if ok is not None:
            score_total += 1

    # 6) module_stats: считаем total/correct по module_id для данной попытки
    db.execute(
        text("DELETE FROM level_exam_attempt_module_stats WHERE attempt_id=:aid"),
        {"aid": attempt_id},
    )

    ms_rows = db.execute(
        text(
            """
            SELECT q.module_id,
                   COUNT(*)::int AS total_cnt,
                   SUM(CASE WHEN q.correct_option_id = a.selected_option_id THEN 1 ELSE 0 END)::int AS correct_cnt
            FROM level_exam_attempt_questions aq
            JOIN questions q ON q.id = aq.question_id
            JOIN level_exam_attempt_answers a ON a.attempt_id = aq.attempt_id AND a.question_id = aq.question_id
            WHERE aq.attempt_id = :aid
            GROUP BY q.module_id
            ORDER BY q.module_id
            """
        ),
        {"aid": attempt_id},
    ).fetchall()

    for module_id, total_cnt, correct_cnt in ms_rows:
        db.execute(
            text(
                """
                INSERT INTO level_exam_attempt_module_stats(attempt_id, module_id, correct_cnt, total_cnt)
                VALUES (:aid, :mid, :cc, :tc)
                """
            ),
            {"aid": attempt_id, "mid": int(module_id), "cc": int(correct_cnt), "tc": int(total_cnt)},
        )

    # 7) фиксируем итог попытки
    passed_now = score_total >= pass_score
    if passed_now:
        db.execute(
            text(
                """
                UPDATE level_exam_attempts
                SET score_total=:score, passed=true, passed_at=now()
                WHERE id=:aid AND passed=false
                """
            ),
            {"score": score_total, "aid": attempt_id},
        )
    else:
        db.execute(
            text(
                """
                UPDATE level_exam_attempts
                SET score_total=:score
                WHERE id=:aid
                """
            ),
            {"score": score_total, "aid": attempt_id},
        )

    # 8) прогрессия (строго после фиксации PASS и в той же транзакции)
    if passed_now:
        progress_action = apply_progress_after_level_exam_pass(
            db,
            user_id=user_id,
            stage_id=stage_id,
            settings_version_id=settings_version_id,
        )
    else:
        progress_action = ProgressAction(action="none", from_stage_id=stage_id, to_stage_id=None)

    # 9) единый return
    return SubmitLevelExamResult(
        attempt_id=attempt_id,
        score_total=score_total,
        pass_score=pass_score,
        passed=passed_now,
        progress=progress_action,
    )