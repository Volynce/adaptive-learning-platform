\# Step-07: Первая ручная миграция DDL (каркас домена)



\## Что сделано

Введена первая ручная миграция Alembic, которая создаёт базовые таблицы и ключевые инварианты домена:



1\) Справочники траектории:

\- tracks

\- stages (unique(track\_id, rank, level))

\- modules (unique(track\_id, name))



2\) Пользователи и админы:

\- users (unique(email), FK track\_id -> tracks)

\- admin\_users (unique(email))



3\) Версионирование настроек:

\- settings\_versions (unique(track\_id, version\_no), CHECK status)

\- track\_settings (1:1 с settings\_versions, FK on delete cascade)



4\) Прогресс обучения:

\- user\_stage\_progress (PK(user\_id, stage\_id), CHECK status)

\- инвариант: у пользователя может быть только одна активная стадия

&nbsp; (partial unique index по user\_id WHERE status='active')



5\) Подтверждения админом:

\- approval\_requests (CHECK type/status, FK к user\_stage\_progress через композитный FK)

\- инвариант: для пары (user\_id, from\_stage\_id) может быть только один pending

&nbsp; (partial unique index WHERE status='pending')



\## Почему миграция ручная (manual-only)

Автогенерация не используется, потому что проект опирается на “жёсткие” инварианты БД:

\- частичные уникальные индексы (partial unique),

\- CHECK ограничения,

\- композитные внешние ключи.

Эти элементы критичны для защиты от гонок (двойной active stage, двойной pending approval, некорректные статусы).



\## Критерии готовности

\- alembic upgrade head выполняется успешно.

\- alembic current показывает head-ревизию.

\- В БД присутствуют созданные таблицы и индексы (проверка через \\dt и \\d).



