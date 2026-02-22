-- Step-20: seed mini-tests (3 вопроса на каждую required статью)
-- Идемпотентность:
-- - сначала проверяем наличие 3 позиций на article_id
-- - если уже есть 3 записи, пропускаем.

DO $$
DECLARE
  r record;
  v_cnt int;
BEGIN
  FOR r IN
    SELECT a.id AS article_id, a.module_id
    FROM articles a
    WHERE a.is_active = true
  LOOP
    SELECT COUNT(*) INTO v_cnt
    FROM article_minitest_questions
    WHERE article_id = r.article_id;

    IF v_cnt >= 3 THEN
      CONTINUE;
    END IF;

    -- выбираем 3 активных вопроса того же module_id
    -- (если вопросов меньше 3 — это ошибка сидинга банка вопросов)
    INSERT INTO article_minitest_questions(article_id, pos, question_id)
    SELECT
      r.article_id,
      ROW_NUMBER() OVER (ORDER BY q.id) AS pos,
      q.id AS question_id
    FROM questions q
    WHERE q.module_id = r.module_id
      AND q.is_active = true
    ORDER BY q.id
    LIMIT 3
    ON CONFLICT (article_id, pos) DO NOTHING;
  END LOOP;
END $$;