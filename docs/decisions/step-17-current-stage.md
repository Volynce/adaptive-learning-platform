\# Step-17: Read-only API текущей стадии (current-stage)



\## Что сделано

1\) Добавлен application/use-case get\_current\_stage():

\- читает user\_stage\_progress(status='active') и join stages/tracks

\- возвращает структурированный результат CurrentStage



2\) Добавлен endpoint GET /api/v1/progress/current-stage (protected):

\- использует current\_user\_id из api/deps.py

\- возвращает DTO CurrentStageResponse



\## Зачем

\- Создать первый доменный read endpoint без модификации данных.

\- Зафиксировать контракт состояния пользователя для будущего web-клиента.

\- Подготовить основу для diagnostika/content/exams, которые завязаны на текущую стадию.



\## Критерий готовности

\- При валидном JWT возвращается текущая активная стадия пользователя

\- Без токена возвращается 401

