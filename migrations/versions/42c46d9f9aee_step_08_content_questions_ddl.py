"""step-08: content + questions ddl

Revision ID: 42c46d9f9aee
Revises: 69ff3174354a
Create Date: 2026-02-16 23:16:41.634142

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42c46d9f9aee'
down_revision: Union[str, Sequence[str], None] = '69ff3174354a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # === 1) Вопросы ===
    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("module_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("correct_option_id", sa.BigInteger(), nullable=True),

        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_questions_module_id_modules"),

        # Инвариант: если вопрос активен, правильный вариант должен быть задан.
        sa.CheckConstraint(
            "is_active = false OR correct_option_id IS NOT NULL",
            name="ck_questions_active_requires_correct",
        ),
    )

    # === 2) Варианты ответов ===
    op.create_table(
        "answer_options",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("pos", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),

        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_answer_options_question_id_questions"),

        # pos должен быть 1..4
        sa.CheckConstraint("pos between 1 and 4", name="ck_answer_options_pos_1_4"),

        # в рамках вопроса позиция уникальна
        sa.UniqueConstraint("question_id", "pos", name="uq_answer_options_question_pos"),

        # нужно для композитного FK (question_id, id)
        sa.UniqueConstraint("question_id", "id", name="uq_answer_options_question_id_id"),
    )

    # === 3) Композитный FK: (questions.id, questions.correct_option_id) -> (answer_options.question_id, answer_options.id)
    # Это гарантирует, что correct_option_id принадлежит тому же question_id.
    op.create_foreign_key(
        "fk_questions_correct_option_belongs_to_question",
        source_table="questions",
        referent_table="answer_options",
        local_cols=["id", "correct_option_id"],
        remote_cols=["question_id", "id"],
        ondelete=None,
    )

    # === 4) Статьи ===
    op.create_table(
        "articles",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column("module_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content_ref", sa.Text(), nullable=False),
        sa.Column("target_rank", sa.Text(), nullable=False),
        sa.Column("target_level", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),

        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_articles_module_id_modules"),
        sa.UniqueConstraint("content_ref", name="uq_articles_content_ref"),
    )

    # === 5) Назначение статей пользователю на стадии ===
    op.create_table(
        "user_stage_articles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("stage_id", sa.BigInteger(), nullable=False),
        sa.Column("article_id", sa.BigInteger(), nullable=False),

        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),

        sa.Column("minitest_passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("minitest_passed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),

        sa.PrimaryKeyConstraint("user_id", "stage_id", "article_id", name="pk_user_stage_articles"),

        # Привязка к прогрессу пользователя на стадии (композитный FK)
        sa.ForeignKeyConstraint(
            ["user_id", "stage_id"],
            ["user_stage_progress.user_id", "user_stage_progress.stage_id"],
            name="fk_user_stage_articles_user_stage_progress",
        ),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], name="fk_user_stage_articles_article_id_articles"),

        sa.CheckConstraint(
            "kind in ('required','optional')",
            name="ck_user_stage_articles_kind",
        ),

        # required: запрещаем read
        sa.CheckConstraint(
            "(kind <> 'required') OR (is_read = false AND read_at IS NULL)",
            name="ck_user_stage_articles_required_no_read",
        ),

        # optional: запрещаем minitest
        sa.CheckConstraint(
            "(kind <> 'optional') OR (minitest_passed = false AND minitest_passed_at IS NULL)",
            name="ck_user_stage_articles_optional_no_minitest",
        ),
    )

    # === 6) Мини-тест статьи (3 вопроса) ===
    op.create_table(
        "article_minitest_questions",
        sa.Column("article_id", sa.BigInteger(), nullable=False),
        sa.Column("pos", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),

        sa.PrimaryKeyConstraint("article_id", "pos", name="pk_article_minitest_questions"),
        sa.ForeignKeyConstraint(["article_id"], ["articles.id"], name="fk_article_minitest_questions_article_id_articles"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_article_minitest_questions_question_id_questions"),

        sa.CheckConstraint("pos between 1 and 3", name="ck_article_minitest_questions_pos_1_3"),
        sa.UniqueConstraint("article_id", "question_id", name="uq_article_minitest_questions_article_question"),
    )


def downgrade() -> None:
    # Откат в обратном порядке зависимостей
    op.drop_table("article_minitest_questions")
    op.drop_table("user_stage_articles")

    op.drop_table("articles")

    # Сначала снимаем FK, потом дропаем таблицы
    op.drop_constraint("fk_questions_correct_option_belongs_to_question", "questions", type_="foreignkey")
    op.drop_table("answer_options")
    op.drop_table("questions")