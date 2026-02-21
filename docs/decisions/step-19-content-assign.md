\# Step-19: Rule-based выдача контента по слабым модулям (не ML)



\## Что сделано

1\) Реализован use-case assign\_content\_for\_current\_stage():

\- источник слабостей: diagnostika\_module\_stats (errors = total\_cnt - correct\_cnt)

\- выбираются K слабых модулей (content\_k\_weak\_modules)

\- optional: по content\_optional\_per\_module на каждый модуль

\- required: по 1 статье на каждый слабый модуль (отдельно от optional)

\- назначения пишутся в user\_stage\_articles



2\) Реализованы API endpoints (protected):

\- POST /api/v1/content/assign

\- GET  /api/v1/content/my

\- POST /api/v1/content/{article\_id}/read (только optional)



3\) Добавлен seed статей для Trainee\_0 (2 статьи на модуль) для воспроизводимого тестирования.



\## Зачем

\- Использовать результаты диагностики как вход в адаптивный трек обучения.

\- Подготовить основу для шагов мини-тестов (required) и допуска к экзаменам.



\## Критерий готовности

\- assign создаёт назначения (optional по всем модулям + required по K слабым)

\- my возвращает список назначенных статей и их статусы

\- read отмечает optional как прочитанную

