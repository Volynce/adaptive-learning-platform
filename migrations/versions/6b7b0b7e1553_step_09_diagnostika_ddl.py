"""step-09: diagnostika ddl

Revision ID: 6b7b0b7e1553
Revises: 42c46d9f9aee
Create Date: 2026-02-16 23:38:07.691059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b7b0b7e1553'
down_revision: Union[str, Sequence[str], None] = '42c46d9f9aee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === 1) diagnostika_results: ровно один раз на пользователя ===
    op.create_table(
        "diagnostika_results",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("stage_id", sa.BigInteger(), nullable=False),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("total_q", sa.Integer(), nullable=False),
        sa.Column("score_total", sa.Integer(), nullable=False),

        # связь с прогрессом пользователя по стадии (композитный FK)
        sa.ForeignKeyConstraint(
            ["user_id", "stage_id"],
            ["user_stage_progress.user_id", "user_stage_progress.stage_id"],
            name="fk_diagnostika_results_user_stage_progress",
        ),

        # диагностика ровно один раз на пользователя (в вашем домене именно так)
        sa.UniqueConstraint("user_id", name="uq_diagnostika_results_user_once"),
    )

    # === 2) diagnostika_attempt_questions: набор вопросов (без дублей) ===
    op.create_table(
        "diagnostika_attempt_questions",
        sa.Column("diagnostika_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),

        sa.PrimaryKeyConstraint("diagnostika_id", "question_id", name="pk_diagnostika_attempt_questions"),

        sa.ForeignKeyConstraint(
            ["diagnostika_id"],
            ["diagnostika_results.id"],
            name="fk_diagnostika_attempt_questions_diagnostika_results",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name="fk_diagnostika_attempt_questions_questions",
        ),
    )

    # === 3) diagnostika_attempt_answers: ответы (один ответ на вопрос в попытке) ===
    # Важный момент: selected_option_id должен принадлежать question_id.
    # Это обеспечивается композитным FK на answer_options(question_id,id).
    op.create_table(
        "diagnostika_attempt_answers",
        sa.Column("diagnostika_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("selected_option_id", sa.BigInteger(), nullable=False),

        sa.PrimaryKeyConstraint("diagnostika_id", "question_id", name="pk_diagnostika_attempt_answers"),

        # ответ возможен только на вопрос, который реально был в попытке
        sa.ForeignKeyConstraint(
            ["diagnostika_id", "question_id"],
            ["diagnostika_attempt_questions.diagnostika_id", "diagnostika_attempt_questions.question_id"],
            name="fk_diagnostika_attempt_answers_to_attempt_questions",
            ondelete="CASCADE",
        ),

        # selected_option_id принадлежит этому question_id
        sa.ForeignKeyConstraint(
            ["question_id", "selected_option_id"],
            ["answer_options.question_id", "answer_options.id"],
            name="fk_diag_ans_selopt_q",
        ),
    )

    # === 4) diagnostika_module_stats: агрегаты по модулям ===
    op.create_table(
        "diagnostika_module_stats",
        sa.Column("diagnostika_id", sa.BigInteger(), nullable=False),
        sa.Column("module_id", sa.BigInteger(), nullable=False),
        sa.Column("correct_cnt", sa.Integer(), nullable=False),
        sa.Column("total_cnt", sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint("diagnostika_id", "module_id", name="pk_diagnostika_module_stats"),

        sa.ForeignKeyConstraint(
            ["diagnostika_id"],
            ["diagnostika_results.id"],
            name="fk_diagnostika_module_stats_diagnostika_results",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["modules.id"],
            name="fk_diagnostika_module_stats_modules",
        ),

        sa.CheckConstraint("correct_cnt >= 0", name="ck_diagnostika_module_stats_correct_nonneg"),
        sa.CheckConstraint("total_cnt >= 0", name="ck_diagnostika_module_stats_total_nonneg"),
        sa.CheckConstraint("correct_cnt <= total_cnt", name="ck_diagnostika_module_stats_correct_le_total"),
    )


def downgrade() -> None:
    op.drop_table("diagnostika_module_stats")
    op.drop_table("diagnostika_attempt_answers")
    op.drop_table("diagnostika_attempt_questions")
    op.drop_table("diagnostika_results")