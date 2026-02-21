from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from adaptive_learning_platform.infrastructure.security.password import hash_password


@dataclass(frozen=True)
class SignupResult:
    user_id: int
    email: str
    full_name: str


class SignupError(Exception):
    """Базовая ошибка регистрации."""


class EmailAlreadyExists(SignupError):
    pass


class MissingBootstrapData(SignupError):
    """
    Нет справочных данных (tracks/stages/settings_versions).
    Это ожидаемо до шага с сидингом.
    """
    pass


def signup(db: Session, *, email: str, full_name: str, password: str) -> SignupResult:
    """
    Минимальный use-case регистрации.

    Делает:
    - проверка уникальности email
    - вставка users (с password_hash)
    - попытка активировать стартовую стадию (если справочники уже засидены)
    """
    # 1) Проверяем email
    row = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).fetchone()
    if row is not None:
        raise EmailAlreadyExists()

    # 2) Находим базовый track (пока самый первый). На этапе с сидингом сделаем детерминированно.
    track_row = db.execute(text("SELECT id FROM tracks ORDER BY id ASC LIMIT 1")).fetchone()
    if track_row is None:
        # Пользователя создать можно, но прогресс — нет. Для устойчивости лучше падать до вставки.
        raise MissingBootstrapData("Нет tracks. Сначала выполните сидинг справочников.")

    track_id = int(track_row[0])

    # 3) Ищем стартовую стадию (минимально: первая по rank/level)
    stage_row = db.execute(
        text("SELECT id FROM stages WHERE track_id = :tid ORDER BY rank ASC, level ASC LIMIT 1"),
        {"tid": track_id},
    ).fetchone()
    if stage_row is None:
        raise MissingBootstrapData("Нет stages. Сначала выполните сидинг справочников.")

    stage_id = int(stage_row[0])

    # 4) Берём активную версию настроек (обязательна по нашей архитектуре)
    sv_row = db.execute(
        text("SELECT id FROM settings_versions WHERE track_id = :tid AND status = 'active' LIMIT 1"),
        {"tid": track_id},
    ).fetchone()
    if sv_row is None:
        raise MissingBootstrapData("Нет active settings_versions для трека. Сначала создайте активную версию настроек.")

    settings_version_id = int(sv_row[0])

    # 5) Вставляем пользователя
    pwd_hash = hash_password(password)
    user_row = db.execute(
        text(
            """
            INSERT INTO users (email, full_name, track_id, password_hash)
            VALUES (:email, :full_name, :track_id, :password_hash)
            RETURNING id
            """
        ),
        {
            "email": email,
            "full_name": full_name,
            "track_id": track_id,
            "password_hash": pwd_hash,
        },
    ).fetchone()

    user_id = int(user_row[0])

    # 6) Активируем прогресс на стартовой стадии
    db.execute(
        text(
            """
            INSERT INTO user_stage_progress (user_id, stage_id, settings_version_id, status)
            VALUES (:uid, :sid, :sv, 'active')
            """
        ),
        {"uid": user_id, "sid": stage_id, "sv": settings_version_id},
    )

    return SignupResult(user_id=user_id, email=email, full_name=full_name)