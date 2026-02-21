\# Step-14: Сидинг справочников и bootstrap настроек (tracks/stages/modules/settings)



\## Что сделано

1\) Добавлен идемпотентный seed-скрипт scripts/seed/step-14-bootstrap.sql:

\- tracks: создаётся default track

\- stages: создаётся Trainee\_0, Junior\_1..3, Middle\_1..3, Senior\_1..3

\- modules: создаются 5 модулей (для соответствия expected\_modules\_count)

\- settings\_versions: создаётся активная версия (если отсутствует)

\- track\_settings: создаются базовые параметры экзаменов/контента



2\) Исправлен выбор стартовой стадии при signup:

\- приоритетно выбирается rank='trainee' AND level=0, чтобы избежать ошибок сортировки rank.



\## Зачем

\- Устранить 412 Precondition Failed для signup и сделать стенд самодостаточным.

\- Зафиксировать минимально необходимую “инициализацию системы” без выполнения сидинга на startup приложения.



\## Критерий готовности

\- seed-скрипт выполняется без ошибок

\- /api/v1/auth/signup возвращает 201 и создаёт user\_stage\_progress(status='active') на Trainee\_0

