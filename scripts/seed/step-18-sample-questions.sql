-- Step-18: sample question bank (минимум 20 вопросов = 5 модулей * 4)
-- Вставка безопасная: вопросы ищутся по (module_id, text).

DO $$
DECLARE
  v_track_id bigint;
  v_module_id bigint;
  v_q_id bigint;
BEGIN
  SELECT id INTO v_track_id FROM tracks WHERE name='default';
  IF v_track_id IS NULL THEN
    RAISE EXCEPTION 'Нет tracks.default — сначала выполните Step-14 seed';
  END IF;

  FOR v_module_id IN
    SELECT id FROM modules WHERE track_id=v_track_id ORDER BY id
  LOOP
    -- 4 вопроса на каждый модуль
    FOR i IN 1..4 LOOP
      -- 1) вопрос (создаём как is_active=false, correct_option_id=NULL)
      SELECT q.id INTO v_q_id
      FROM questions q
      WHERE q.module_id = v_module_id
        AND q.text = format('Q%s (module %s)', i, v_module_id)
      LIMIT 1;

      IF v_q_id IS NULL THEN
        INSERT INTO questions(module_id, text, is_active, correct_option_id)
        VALUES (v_module_id, format('Q%s (module %s)', i, v_module_id), false, NULL)
        RETURNING id INTO v_q_id;
      END IF;

      -- 2) варианты 1..4
      INSERT INTO answer_options(question_id, pos, text)
      VALUES
        (v_q_id, 1, 'Option A'),
        (v_q_id, 2, 'Option B'),
        (v_q_id, 3, 'Option C'),
        (v_q_id, 4, 'Option D')
      ON CONFLICT (question_id, pos) DO NOTHING;

      -- 3) назначаем правильный ответ (pos=1) и активируем вопрос
      UPDATE questions q
      SET correct_option_id = ao.id,
          is_active = true
      FROM answer_options ao
      WHERE q.id = v_q_id
        AND ao.question_id = v_q_id
        AND ao.pos = 1;
    END LOOP;
  END LOOP;
END $$;