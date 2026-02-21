-- Step-19: sample articles (минимум 2 статьи на модуль для Trainee_0)
-- Articles.kind хранится в user_stage_articles, поэтому здесь просто создаём пул статей.

DO $$
DECLARE
  v_track_id bigint;
  r record;
BEGIN
  SELECT id INTO v_track_id FROM tracks WHERE name='default';
  IF v_track_id IS NULL THEN
    RAISE EXCEPTION 'Нет tracks.default — сначала выполните Step-14 seed';
  END IF;

  FOR r IN SELECT id, name FROM modules WHERE track_id=v_track_id ORDER BY id LOOP
    -- 1) "Optional-like" статья
    INSERT INTO articles(module_id, title, content_ref, target_rank, target_level, is_active)
    VALUES (
      r.id,
      format('Введение (%s) — optional', r.name),
      format('local://articles/%s/intro', r.name),
      'trainee',
      0,
      true
    )
    ON CONFLICT (content_ref) DO NOTHING;

    -- 2) "Required-like" статья
    INSERT INTO articles(module_id, title, content_ref, target_rank, target_level, is_active)
    VALUES (
      r.id,
      format('Практика (%s) — required', r.name),
      format('local://articles/%s/practice', r.name),
      'trainee',
      0,
      true
    )
    ON CONFLICT (content_ref) DO NOTHING;
  END LOOP;
END $$;