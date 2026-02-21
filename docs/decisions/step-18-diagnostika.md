\# Step-18: Входная диагностика (start/submit) + статистика ошибок



\## Что сделано

1\) Реализован use-case start diagnostika:

\- допускается только на Trainee\_0 (rank='trainee', level=0)

\- создаётся diagnostika\_results (уникально по user\_id, только один раз)

\- генерируется набор вопросов по track\_settings (entry\_total\_q, entry\_per\_module\_q)

\- записываются diagnostika\_attempt\_questions

\- пользователю возвращаются вопросы и варианты ответов



2\) Реализован use-case submit diagnostika:

\- принимаются ответы

\- записываются diagnostika\_attempt\_answers (FK гарантирует принадлежность вопросов попытке)

\- вычисляется score\_total и пишется в diagnostika\_results

\- вычисляется статистика по модулям и пишется diagnostika\_module\_stats



3\) Добавлены API endpoints:

\- POST /api/v1/diagnostika/start (protected)

\- POST /api/v1/diagnostika/submit (protected)



\## Зачем

\- Создать первый полноценный доменный сценарий с записью попытки и метрик слабости.

\- Подготовить данные для адаптивной выдачи контента и экзаменов.



\## Критерий готовности

\- start возвращает diagnostika\_id и список вопросов

\- submit сохраняет ответы, считает score\_total и module\_stats

\- повторный start возвращает 409 (диагностика один раз)

