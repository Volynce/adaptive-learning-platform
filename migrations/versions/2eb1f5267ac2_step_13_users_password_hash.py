"""step-13: users password_hash

Revision ID: 2eb1f5267ac2
Revises: 35ed1964802a
Create Date: 2026-02-21 13:16:00.147010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2eb1f5267ac2'
down_revision: Union[str, Sequence[str], None] = '12fe7d06e671'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем хеш пароля. Важно: пароль в чистом виде не храним.
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=False))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
