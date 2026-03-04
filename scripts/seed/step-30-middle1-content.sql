-- Step-30 seed: Middle_1 content pack (target_rank='middle', target_level=1)
-- Цель: дать content/assign достаточное число статей для optional+required по каждому module трека.
-- Идемпотентно: используем UNIQUE(content_ref) + ON CONFLICT DO NOTHING.

-- 1) OPTIONAL: 2 статьи на каждый module (с запасом, если optional_per_module = 1..2)
INSERT INTO public.articles (module_id, title, content_ref, target_rank, target_level)
SELECT m.id,
       format('Middle 1 — %s — Optional 01', m.name),
       format('middle1-mod%s-opt-01', m.id),
       'middle',
       1
FROM public.modules m
WHERE m.track_id = 1
ON CONFLICT (content_ref) DO NOTHING;

INSERT INTO public.articles (module_id, title, content_ref, target_rank, target_level)
SELECT m.id,
       format('Middle 1 — %s — Optional 02', m.name),
       format('middle1-mod%s-opt-02', m.id),
       'middle',
       1
FROM public.modules m
WHERE m.track_id = 1
ON CONFLICT (content_ref) DO NOTHING;

-- 2) REQUIRED candidate: 1 статья на каждый module (чтобы K weak modules точно имели 1 required)
INSERT INTO public.articles (module_id, title, content_ref, target_rank, target_level)
SELECT m.id,
       format('Middle 1 — %s — Required 01', m.name),
       format('middle1-mod%s-req-01', m.id),
       'middle',
       1
FROM public.modules m
WHERE m.track_id = 1
ON CONFLICT (content_ref) DO NOTHING;

-- 3) Привязка minitest: 3 вопроса к каждой required статье (по модулю).
-- Берём первые 3 активных вопроса модуля (is_active=true, correct_option_id NOT NULL).
WITH req AS (
  SELECT a.id AS article_id, a.module_id
  FROM public.articles a
  WHERE a.target_rank='middle'
    AND a.target_level=1
    AND a.content_ref LIKE 'middle1-mod%-req-01'
),
picked AS (
  SELECT r.article_id,
         q.id AS question_id,
         row_number() OVER (PARTITION BY r.article_id ORDER BY q.id) AS pos
  FROM req r
  JOIN LATERAL (
    SELECT id
    FROM public.questions
    WHERE module_id=r.module_id AND is_active=true AND correct_option_id IS NOT NULL
    ORDER BY id
    LIMIT 3
  ) q ON true
)
INSERT INTO public.article_minitest_questions(article_id, pos, question_id)
SELECT article_id, pos, question_id
FROM picked
ON CONFLICT DO NOTHING;