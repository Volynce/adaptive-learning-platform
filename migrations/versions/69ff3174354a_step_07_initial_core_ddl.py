"""step-07: initial core ddl

Revision ID: 69ff3174354a
Revises: 
Create Date: 2026-02-16 23:08:18.715500

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69ff3174354a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === 1) Справочники траектории ===

    op.create_table(
        "tracks",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.UniqueConstraint("name", name="uq_tracks_name"),
    )

    op.create_table(
        "stages",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("track_id", sa.BigInteger(), nullable=False),
        sa.Column("rank", sa.Text(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], name="fk_stages_track_id_tracks"),
        sa.UniqueConstraint("track_id", "rank", "level", name="uq_stages_track_rank_level"),
    )

    op.create_table(
        "modules",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("track_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], name="fk_modules_track_id_tracks"),
        sa.UniqueConstraint("track_id", "name", name="uq_modules_track_name"),
    )

    # === 2) Пользователи и админы ===

    op.create_table(
        "admin_users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_admin_users_email"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("track_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("graduated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], name="fk_users_track_id_tracks"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # === 3) Версионирование настроек трека ===

    op.create_table(
        "settings_versions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("track_id", sa.BigInteger(), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),

        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], name="fk_settings_versions_track_id_tracks"),
        sa.ForeignKeyConstraint(
            ["created_by_admin_id"], ["admin_users.id"], name="fk_settings_versions_created_by_admin_id_admin_users"
        ),

        sa.CheckConstraint(
            "status in ('draft','active','archived')",
            name="ck_settings_versions_status",
        ),
        sa.UniqueConstraint("track_id", "version_no", name="uq_settings_versions_track_version"),
    )

    # Частичная уникальность: на один track_id только одна активная версия настроек
    op.create_index(
        "uq_settings_versions_active_per_track",
        "settings_versions",
        ["track_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "track_settings",
        sa.Column("settings_version_id", sa.BigInteger(), primary_key=True),

        sa.Column("expected_modules_count", sa.Integer(), nullable=False),

        sa.Column("entry_total_q", sa.Integer(), nullable=False),
        sa.Column("entry_per_module_q", sa.Integer(), nullable=False),

        sa.Column("level_exam_total_q", sa.Integer(), nullable=False),
        sa.Column("level_exam_pass_score", sa.Integer(), nullable=False),
        sa.Column("k_exam", sa.Integer(), nullable=False),
        sa.Column("level_exam_min_per_module", sa.Integer(), nullable=False),
        sa.Column("level_exam_max_per_module", sa.Integer(), nullable=False),

        sa.Column("rank_final_total_q", sa.Integer(), nullable=False),
        sa.Column("rank_final_pass_score", sa.Integer(), nullable=False),
        sa.Column("k_final", sa.Integer(), nullable=False),
        sa.Column("rank_final_min_per_module", sa.Integer(), nullable=False),
        sa.Column("rank_final_max_per_module", sa.Integer(), nullable=False),

        sa.Column("content_k_weak_modules", sa.Integer(), nullable=False),
        sa.Column("content_optional_per_module", sa.Integer(), nullable=False),

        sa.Column("weakness_metric", sa.Text(), nullable=False, server_default=sa.text("'errors'")),

        sa.ForeignKeyConstraint(
            ["settings_version_id"],
            ["settings_versions.id"],
            name="fk_track_settings_settings_version_id_settings_versions",
            ondelete="CASCADE",
        ),
    )

    # === 4) Прогресс пользователя по стадиям + инварианты (одна active стадия) ===

    op.create_table(
        "user_stage_progress",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("stage_id", sa.BigInteger(), nullable=False),
        sa.Column("settings_version_id", sa.BigInteger(), nullable=False),

        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint("user_id", "stage_id", name="pk_user_stage_progress"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_stage_progress_user_id_users"),
        sa.ForeignKeyConstraint(["stage_id"], ["stages.id"], name="fk_user_stage_progress_stage_id_stages"),
        sa.ForeignKeyConstraint(
            ["settings_version_id"],
            ["settings_versions.id"],
            name="fk_user_stage_progress_settings_version_id_settings_versions",
        ),

        sa.CheckConstraint(
            "status in ('active','pending_approval','completed')",
            name="ck_user_stage_progress_status",
        ),
    )

    # Частичная уникальность: у пользователя только одна активная стадия
    op.create_index(
        "uq_user_stage_progress_one_active_per_user",
        "user_stage_progress",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    # === 5) Запросы на подтверждение (approvals) ===

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),

        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("from_stage_id", sa.BigInteger(), nullable=False),
        sa.Column("to_stage_id", sa.BigInteger(), nullable=True),

        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_admin_id", sa.BigInteger(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),

        # Связь с прогрессом пользователя (композитный FK)
        sa.ForeignKeyConstraint(
            ["user_id", "from_stage_id"],
            ["user_stage_progress.user_id", "user_stage_progress.stage_id"],
            name="fk_approval_requests_user_from_stage_user_stage_progress",
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_admin_id"],
            ["admin_users.id"],
            name="fk_approval_requests_approved_by_admin_id_admin_users",
        ),

        sa.CheckConstraint(
            "type in ('rank_transition','graduation')",
            name="ck_approval_requests_type",
        ),
        sa.CheckConstraint(
            "status in ('pending','approved')",
            name="ck_approval_requests_status",
        ),
    )

    # Частичная уникальность: для (user_id, from_stage_id) только один pending запрос
    op.create_index(
        "uq_approval_requests_one_pending_per_from_stage",
        "approval_requests",
        ["user_id", "from_stage_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    # Откат идёт в обратном порядке зависимостей
    op.drop_index("uq_approval_requests_one_pending_per_from_stage", table_name="approval_requests")
    op.drop_table("approval_requests")

    op.drop_index("uq_user_stage_progress_one_active_per_user", table_name="user_stage_progress")
    op.drop_table("user_stage_progress")

    op.drop_table("track_settings")

    op.drop_index("uq_settings_versions_active_per_track", table_name="settings_versions")
    op.drop_table("settings_versions")

    op.drop_table("users")
    op.drop_table("admin_users")

    op.drop_table("modules")
    op.drop_table("stages")
    op.drop_table("tracks")