-- Step-27: Junior_2 content seed (rank=junior, level=2)
-- Цель: чтобы /content/assign смог назначить optional (>= content_optional_per_module на модуль),
-- а для weak-модулей смог взять ещё одну статью как required (то есть нужно минимум 2 статьи на модуль).

BEGIN;

-- 1) OPTIONAL: 1 статья на каждый модуль (junior_2)
INSERT INTO articles(module_id, title, content_ref, target_rank, target_level, is_active)
SELECT
  m.id,
  format('Введение (%s) — optional', m.name),
  ('local://articles/' || m.name || '/junior-2/intro'),
  'junior',
  2,
  true
FROM modules m
WHERE NOT EXISTS (
  SELECT 1
  FROM articles a
  WHERE a.content_ref = ('local://articles/' || m.name || '/junior-2/intro')
);

-- 2) PRACTICE REQUIRED: ещё 1 статья на каждый модуль (из неё будет required для слабых модулей)
INSERT INTO articles(module_id, title, content_ref, target_rank, target_level, is_active)
SELECT
  m.id,
  format('Практика (%s) — required', m.name),
  ('local://articles/' || m.name || '/junior-2/practice'),
  'junior',
  2,
  true
FROM modules m
WHERE NOT EXISTS (
  SELECT 1
  FROM articles a
  WHERE a.content_ref = ('local://articles/' || m.name || '/junior-2/practice')
);

-- 3) MINITEST (3 вопроса) для practice-статей junior_2
-- ВНИМАНИЕ: структура article_minitest_questions может быть:
--   A) (article_id, question_id)
--   B) (article_id, question_id, pos)
-- Посмотрите структуру командой: \d article_minitest_questions
-- и используйте подходящий блок ниже.

-- === Вариант A: если таблица БЕЗ pos ===
-- INSERT INTO article_minitest_questions(article_id, question_id)
-- SELECT
--   a.id,
--   q.id
-- FROM articles a
-- JOIN LATERAL (
--   SELECT qq.id
--   FROM questions qq
--   WHERE qq.module_id = a.module_id AND qq.is_active = true
--   ORDER BY qq.id
--   LIMIT 3
-- ) q ON true
-- WHERE a.target_rank='junior' AND a.target_level=2
--   AND a.content_ref LIKE 'local://articles/%/junior-2/practice'
--   AND NOT EXISTS (
--     SELECT 1 FROM article_minitest_questions amq WHERE amq.article_id = a.id
--   );

-- === Вариант B: если таблица С pos ===
INSERT INTO article_minitest_questions(article_id, question_id, pos)
SELECT
  a.id,
  q.id,
  q.pos
FROM articles a
JOIN LATERAL (
  SELECT
    qq.id,
    row_number() OVER (ORDER BY qq.id) AS pos
  FROM questions qq
  WHERE qq.module_id = a.module_id AND qq.is_active = true
  ORDER BY qq.id
  LIMIT 3
) q ON true
WHERE a.target_rank='junior' AND a.target_level=2
  AND a.content_ref LIKE 'local://articles/%/junior-2/practice'
  AND NOT EXISTS (
    SELECT 1 FROM article_minitest_questions amq WHERE amq.article_id = a.id
  );

COMMIT;