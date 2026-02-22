"""step-25: admin password_hash

Revision ID: 52fec2dfc3d9
Revises: 2eb1f5267ac2
Create Date: 2026-02-22 20:29:20.398292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52fec2dfc3d9'
down_revision: Union[str, Sequence[str], None] = '2eb1f5267ac2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем password_hash для админа (для /api/v1/admin/login).
    # На учебном стенде допускаем NULL только если старые строки уже существуют.
    # В дальнейшем можно ужесточить до NOT NULL после сидинга.
    op.add_column("admin_users", sa.Column("password_hash", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("admin_users", "password_hash")
