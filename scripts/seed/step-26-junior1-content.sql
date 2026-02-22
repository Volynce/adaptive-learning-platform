-- Step-26: статьи + minitest для junior_1 (rank='junior', level=1)

-- optional
INSERT INTO articles(module_id, title, content_ref, target_rank, target_level, is_active, created_at)
SELECT
  m.id,
  'Введение (' || m.name || ') — optional (junior_1)',
  'local://articles/junior-1/' || m.name || '/intro',
  'junior',
  1,
  true,
  now()
FROM modules m
WHERE m.track_id = 1
ON CONFLICT (content_ref) DO NOTHING;

-- required
INSERT INTO articles(module_id, title, content_ref, target_rank, target_level, is_active, created_at)
SELECT
  m.id,
  'Практика (' || m.name || ') — required (junior_1)',
  'local://articles/junior-1/' || m.name || '/practice',
  'junior',
  1,
  true,
  now()
FROM modules m
WHERE m.track_id = 1
ON CONFLICT (content_ref) DO NOTHING;

-- minitest 3/3 для required junior_1
WITH required_articles AS (
  SELECT a.id AS article_id, a.module_id
  FROM articles a
  WHERE a.target_rank='junior'
    AND a.target_level=1
    AND a.content_ref LIKE 'local://articles/junior-1/%/practice'
),
q3 AS (
  SELECT
    q.id AS question_id,
    q.module_id,
    row_number() OVER (PARTITION BY q.module_id ORDER BY q.id) AS rn
  FROM questions q
)
INSERT INTO article_minitest_questions(article_id, pos, question_id)
SELECT
  ra.article_id,
  q3.rn AS pos,
  q3.question_id
FROM required_articles ra
JOIN q3 ON q3.module_id = ra.module_id AND q3.rn <= 3
ON CONFLICT DO NOTHING;