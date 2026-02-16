\# Step-09: DDL диагностики (diagnostika\_\*)



\## Что добавлено

1\) diagnostika\_results

\- диагностика ровно один раз на пользователя (UNIQUE user\_id)

\- привязка к user\_stage\_progress через композитный FK (user\_id, stage\_id)



2\) diagnostika\_attempt\_questions

\- набор вопросов диагностики

\- PK(diagnostika\_id, question\_id) запрещает дубли вопросов в попытке



3\) diagnostika\_attempt\_answers

\- ответы на вопросы диагностики

\- FK на attempt\_questions: нельзя ответить на вопрос, которого не было в попытке

\- композитный FK (question\_id, selected\_option\_id) -> answer\_options(question\_id, id)

&nbsp; гарантирует, что выбранный вариант относится к этому question\_id

\- правило именования: имена constraints держим короче 63 символов (ограничение PostgreSQL)



4\) diagnostika\_module\_stats

\- агрегаты по модулям (correct/total)

\- CHECK: 0 <= correct\_cnt <= total\_cnt



\## Критерий готовности

\- alembic upgrade head проходит

\- alembic current показывает head ревизию шага

\- diagnostika\_\* таблицы присутствуют в БД



