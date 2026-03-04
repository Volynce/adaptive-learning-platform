\# Step-31: Переход middle\_2 → middle\_3 через auto-advance (within rank)



\## Что сделано



1\) Зафиксирован доменный сценарий прогрессии \*\*внутри ранга\*\* после PASS level-exam на стадии rank='middle', level=2:

\- при успешном сабмите level-exam система автоматически завершает текущую стадию `middle\_2`;

\- активирует следующую стадию `middle\_3` без создания `approval\_requests`.



2\) End-to-end прогон на пользователе `seedtest3@example.com`:

\- подтверждено состояние `middle\_2` (`GET /api/v1/progress/current-stage`);

\- выполнено назначение контента `POST /api/v1/content/assign`;

\- закрыты optional статьи через `POST /api/v1/content/{article\_id}/read`;

\- закрыты required статьи через `POST /api/v1/content/{article\_id}/minitest/submit` (PASS 3/3);

\- подтвержден допуск `GET /api/v1/progress/eligibility -> eligible=true`;

\- выполнен `POST /api/v1/exams/level/start` и `POST /api/v1/exams/level/{attempt\_id}/submit` (PASS).



3\) Проверка результата:

\- `GET /api/v1/progress/current-stage` показывает `rank='middle', level=3`;

\- в `user\_stage\_progress` соблюдён инвариант: ровно одна активная стадия на пользователя;

\- `approval\_requests` для данного перехода не создаётся (approval используется только на границах рангов).



\## Зачем



\- Подтвердить поведение “within rank”: level 2→3 прогрессируется автоматически.

\- Зафиксировать воспроизводимый e2e сценарий для регрессии и подготовки к ML.



\## Критерий готовности



\- После PASS level-exam на `middle\_2` активная стадия становится `middle\_3` без approvals.

\- `GET /api/v1/progress/current-stage` возвращает `rank='middle', level=3`.



\## Артефакты



\- docs/decisions/step-31-middle2-to-middle3-e2e.md

\- scripts/seed/step-31-middle2-content.sql (если потребовался для assign)

