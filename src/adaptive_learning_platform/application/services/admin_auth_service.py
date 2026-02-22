from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from adaptive_learning_platform.infrastructure.security.password import verify_password
from adaptive_learning_platform.infrastructure.security.jwt import create_access_token


class AdminAuthError(Exception):
    pass


class AdminNotFound(AdminAuthError):
    pass


class AdminInactive(AdminAuthError):
    pass


class InvalidAdminCredentials(AdminAuthError):
    pass


@dataclass(frozen=True)
class AdminLoginResult:
    admin_id: int
    access_token: str


def admin_login(db: Session, *, email: str, password: str) -> AdminLoginResult:
    row = db.execute(
        text(
            """
            SELECT id, password_hash, is_active
            FROM admin_users
            WHERE email = :email
            """
        ),
        {"email": email},
    ).fetchone()

    if row is None:
        raise AdminNotFound("Администратор не найден")

    admin_id = int(row[0])
    pwd_hash = row[1]
    is_active = bool(row[2])

    if not is_active:
        raise AdminInactive("Администратор отключён")

    if not pwd_hash:
        raise InvalidAdminCredentials("У администратора не задан пароль")

    if not verify_password(password, pwd_hash):
        raise InvalidAdminCredentials("Неверный пароль")

    token = create_access_token(subject=str(admin_id), scope="admin")
    return AdminLoginResult(admin_id=admin_id, access_token=token)