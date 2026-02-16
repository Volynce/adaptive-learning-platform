"""step-10: level exam ddl

Revision ID: 7d2ed93fb320
Revises: 6b7b0b7e1553
Create Date: 2026-02-16 23:44:12.476938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d2ed93fb320'
down_revision: Union[str, Sequence[str], None] = '6b7b0b7e1553'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === 1) level_exam_attempts ===
    op.create_table(
        "level_exam_attempts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),

        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("stage_id", sa.BigInteger(), nullable=False),

        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),

        sa.Column("score_total", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("passed_at", sa.DateTime(timezone=True), nullable=True),

        # попытка привязана к прогрессу пользователя на стадии
        sa.ForeignKeyConstraint(
            ["user_id", "stage_id"],
            ["user_stage_progress.user_id", "user_stage_progress.stage_id"],
            name="fk_lexam_att_usp",
        ),

        sa.UniqueConstraint("user_id", "stage_id", "attempt_no", name="uq_lexam_att_no"),

        sa.CheckConstraint("attempt_no >= 1", name="ck_lexam_att_no_ge1"),
        sa.CheckConstraint("score_total >= 0", name="ck_lexam_score_ge0"),
        sa.CheckConstraint("passed = false OR passed_at IS NOT NULL", name="ck_lexam_passed_has_ts"),
    )

    # PASSED только один раз на (user_id, stage_id)
    op.create_index(
        "uq_lexam_passed_once",
        "level_exam_attempts",
        ["user_id", "stage_id"],
        unique=True,
        postgresql_where=sa.text("passed = true"),
    )

    # === 2) level_exam_attempt_questions ===
    op.create_table(
        "level_exam_attempt_questions",
        sa.Column("attempt_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),

        sa.PrimaryKeyConstraint("attempt_id", "question_id", name="pk_lexam_att_q"),

        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["level_exam_attempts.id"],
            name="fk_lexam_att_q_att",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name="fk_lexam_att_q_q",
        ),
    )

    # === 3) level_exam_attempt_answers ===
    op.create_table(
        "level_exam_attempt_answers",
        sa.Column("attempt_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("selected_option_id", sa.BigInteger(), nullable=False),

        sa.PrimaryKeyConstraint("attempt_id", "question_id", name="pk_lexam_att_ans"),

        # нельзя ответить на вопрос, которого не было в попытке
        sa.ForeignKeyConstraint(
            ["attempt_id", "question_id"],
            ["level_exam_attempt_questions.attempt_id", "level_exam_attempt_questions.question_id"],
            name="fk_lexam_ans_attq",
            ondelete="CASCADE",
        ),

        # выбранный вариант принадлежит этому question_id
        sa.ForeignKeyConstraint(
            ["question_id", "selected_option_id"],
            ["answer_options.question_id", "answer_options.id"],
            name="fk_lexam_ans_opt",
        ),
    )

    # === 4) level_exam_attempt_module_stats ===
    op.create_table(
        "level_exam_attempt_module_stats",
        sa.Column("attempt_id", sa.BigInteger(), nullable=False),
        sa.Column("module_id", sa.BigInteger(), nullable=False),
        sa.Column("correct_cnt", sa.Integer(), nullable=False),
        sa.Column("total_cnt", sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint("attempt_id", "module_id", name="pk_lexam_mod_stats"),

        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["level_exam_attempts.id"],
            name="fk_lexam_mod_att",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["modules.id"],
            name="fk_lexam_mod_mod",
        ),

        sa.CheckConstraint("correct_cnt >= 0", name="ck_lexam_mod_cor_ge0"),
        sa.CheckConstraint("total_cnt >= 0", name="ck_lexam_mod_tot_ge0"),
        sa.CheckConstraint("correct_cnt <= total_cnt", name="ck_lexam_mod_cor_le_tot"),
    )


def downgrade() -> None:
    op.drop_table("level_exam_attempt_module_stats")
    op.drop_table("level_exam_attempt_answers")
    op.drop_table("level_exam_attempt_questions")

    op.drop_index("uq_lexam_passed_once", table_name="level_exam_attempts")
    op.drop_table("level_exam_attempts")