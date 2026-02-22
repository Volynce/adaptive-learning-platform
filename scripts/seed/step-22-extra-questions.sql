-- Step-22: расширение банка вопросов
-- Цель: в каждом модуле довести количество активных вопросов минимум до 8.
-- Важно: questions имеет CHECK: активный вопрос обязан иметь correct_option_id.
-- Поэтому вставляем вопрос как is_active=false, затем создаём варианты, затем делаем is_active=true и ставим correct_option_id.

DO $$
DECLARE
  r record;
  existing int;
  target int := 8;
  n int;
  qid bigint;
  opt1 bigint;
BEGIN
  FOR r IN
    SELECT id AS module_id
    FROM modules
    ORDER BY id
  LOOP
    SELECT COUNT(*) INTO existing
    FROM questions
    WHERE module_id = r.module_id;

    n := existing + 1;

    WHILE existing < target LOOP
      INSERT INTO questions(module_id, text, is_active, correct_option_id)
      VALUES (
        r.module_id,
        format('Q%s (module %s) [seed extra]', n, r.module_id),
        false,
        NULL
      )
      RETURNING id INTO qid;

      -- pos=1 сохраняем как correct_option_id
      INSERT INTO answer_options(question_id, pos, text)
      VALUES (qid, 1, 'Option A')
      RETURNING id INTO opt1;

      INSERT INTO answer_options(question_id, pos, text)
      VALUES
        (qid, 2, 'Option B'),
        (qid, 3, 'Option C'),
        (qid, 4, 'Option D');

      UPDATE questions
      SET correct_option_id = opt1,
          is_active = true
      WHERE id = qid;

      existing := existing + 1;
      n := n + 1;
    END LOOP;
  END LOOP;
END $$;