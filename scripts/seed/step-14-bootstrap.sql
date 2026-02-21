-- Step-14: bootstrap seed (tracks/stages/modules/settings_versions/track_settings)
-- Принцип: можно запускать повторно (ON CONFLICT / проверки существования)

DO $$
DECLARE
  v_track_id bigint;
  v_settings_version_id bigint;
  v_next_version int;
BEGIN
  --------------------------------------------------------------------
  -- 1) Track
  --------------------------------------------------------------------
  SELECT id INTO v_track_id
  FROM tracks
  WHERE name = 'default';

  IF v_track_id IS NULL THEN
    INSERT INTO tracks(name)
    VALUES ('default')
    RETURNING id INTO v_track_id;
  END IF;

  --------------------------------------------------------------------
  -- 2) Stages: Trainee_0 -> Junior_1..3 -> Middle_1..3 -> Senior_1..3
  -- Важно: rank значения фиксируем как: trainee/junior/middle/senior
  --------------------------------------------------------------------
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'trainee', 0)
  ON CONFLICT (track_id, rank, level) DO NOTHING;

  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'junior', 1)
  ON CONFLICT (track_id, rank, level) DO NOTHING;
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'junior', 2)
  ON CONFLICT (track_id, rank, level) DO NOTHING;
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'junior', 3)
  ON CONFLICT (track_id, rank, level) DO NOTHING;

  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'middle', 1)
  ON CONFLICT (track_id, rank, level) DO NOTHING;
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'middle', 2)
  ON CONFLICT (track_id, rank, level) DO NOTHING;
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'middle', 3)
  ON CONFLICT (track_id, rank, level) DO NOTHING;

  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'senior', 1)
  ON CONFLICT (track_id, rank, level) DO NOTHING;
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'senior', 2)
  ON CONFLICT (track_id, rank, level) DO NOTHING;
  INSERT INTO stages(track_id, rank, level) VALUES (v_track_id, 'senior', 3)
  ON CONFLICT (track_id, rank, level) DO NOTHING;

  --------------------------------------------------------------------
  -- 3) Modules (минимальный набор 5 модулей)
  --------------------------------------------------------------------
  INSERT INTO modules(track_id, name) VALUES (v_track_id, 'python-basics')
  ON CONFLICT (track_id, name) DO NOTHING;
  INSERT INTO modules(track_id, name) VALUES (v_track_id, 'sql-basics')
  ON CONFLICT (track_id, name) DO NOTHING;
  INSERT INTO modules(track_id, name) VALUES (v_track_id, 'backend-architecture')
  ON CONFLICT (track_id, name) DO NOTHING;
  INSERT INTO modules(track_id, name) VALUES (v_track_id, 'testing')
  ON CONFLICT (track_id, name) DO NOTHING;
  INSERT INTO modules(track_id, name) VALUES (v_track_id, 'devops')
  ON CONFLICT (track_id, name) DO NOTHING;

  --------------------------------------------------------------------
  -- 4) settings_versions: нужна одна active версия для трека
  --------------------------------------------------------------------
  SELECT id INTO v_settings_version_id
  FROM settings_versions
  WHERE track_id = v_track_id AND status = 'active'
  LIMIT 1;

  IF v_settings_version_id IS NULL THEN
    SELECT COALESCE(MAX(version_no), 0) + 1 INTO v_next_version
    FROM settings_versions
    WHERE track_id = v_track_id;

    INSERT INTO settings_versions(track_id, version_no, status, note)
    VALUES (v_track_id, v_next_version, 'active', 'bootstrap active settings')
    RETURNING id INTO v_settings_version_id;
  END IF;

  --------------------------------------------------------------------
  -- 5) track_settings: 1:1 с settings_versions
  --------------------------------------------------------------------
  INSERT INTO track_settings(
    settings_version_id,
    expected_modules_count,
    entry_total_q,
    entry_per_module_q,
    level_exam_total_q,
    level_exam_pass_score,
    k_exam,
    level_exam_min_per_module,
    level_exam_max_per_module,
    rank_final_total_q,
    rank_final_pass_score,
    k_final,
    rank_final_min_per_module,
    rank_final_max_per_module,
    content_k_weak_modules,
    content_optional_per_module
  )
  VALUES (
    v_settings_version_id,
    5,
    20,
    4,
    20,
    15,
    3,
    3,
    6,
    40,
    30,
    3,
    6,
    12,
    3,
    1
  )
  ON CONFLICT (settings_version_id) DO NOTHING;

END $$;