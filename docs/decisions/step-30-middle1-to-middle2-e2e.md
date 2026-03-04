\# Step-30: Переход middle\_1 → middle\_2 через auto-advance (within rank)



\## Что сделано



1\) Зафиксирован доменный сценарий прогрессии \*\*внутри ранга\*\* после PASS level-exam на стадии rank='middle', level=1:

\- при успешном сабмите level-exam система \*\*автоматически\*\* завершает текущую стадию `middle\\\_1`;

\- активирует следующую стадию `middle\\\_2` без создания `approval\\\_requests`.



2\) End-to-end прогон на пользователе `seedtest3@example.com`:

\- подтверждено, что пользователь находится на `middle\\\_1` (`GET /api/v1/progress/current-stage`);

\- выполнено назначение контента `POST /api/v1/content/assign`;

\- закрыты optional статьи через `POST /api/v1/content/{article\\\_id}/read`;

\- закрыты required статьи через `POST /api/v1/content/{article\\\_id}/minitest/submit` (PASS 3/3);

\- подтвержден допуск `GET /api/v1/progress/eligibility -> eligible=true`;

\- выполнен `POST /api/v1/exams/level/start` и `POST /api/v1/exams/level/{attempt\\\_id}/submit` (PASS).



3\) Проверка результата:

\- `GET /api/v1/progress/current-stage` показывает `rank='middle', level=2`;

\- в БД `user\\\_stage\\\_progress`:

  - `middle\\\_1` переведён в `status='completed'`;

  - `middle\\\_2` активирован как `status='active'`;

\- `approval\\\_requests` для данного перехода не создаётся (approval используется только на границах рангов).



\## Зачем



\- Развести два типа прогрессии:

  1) Внутри ранга (level 1→2→3) — автоматическая прогрессия (`auto\\\_advanced`).

  2) Между рангами (junior→middle→senior) — прогрессия только через approvals.



\- Зафиксировать воспроизводимый e2e сценарий для регрессии и подготовки к ML (данные попыток/результатов консистентны).



\## Критерий готовности



\- После PASS level-exam на `middle\\\_1` активная стадия становится `middle\\\_2` без approvals.

\- `GET /api/v1/progress/current-stage` возвращает `rank='middle', level=2`.

\- В `user\\\_stage\\\_progress` соблюдён инвариант: ровно одна `status='active'` стадия на пользователя.



\## Артефакты



\- docs/decisions/step-30-middle1-to-middle2-e2e.md

