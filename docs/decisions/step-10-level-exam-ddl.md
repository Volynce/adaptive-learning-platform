\# Step-10: DDL экзамена уровня (level\_exam\_\*)



\## Что добавлено

1\) level\_exam\_attempts

\- попытки экзамена уровня по (user\_id, stage\_id)

\- UNIQUE(user\_id, stage\_id, attempt\_no)

\- partial UNIQUE(user\_id, stage\_id) WHERE passed=true (PASS фиксируется один раз)

\- CHECK: attempt\_no>=1, score\_total>=0, passed=>passed\_at not null



2\) level\_exam\_attempt\_questions

\- состав вопросов попытки

\- PK(attempt\_id, question\_id) запрещает повторы вопросов внутри попытки



3\) level\_exam\_attempt\_answers

\- ответы по вопросам попытки

\- FK(attempt\_id, question\_id) -> attempt\_questions: нельзя ответить на вопрос, которого не было

\- композитный FK(question\_id, selected\_option\_id) -> answer\_options(question\_id, id):

&nbsp; выбранный вариант принадлежит этому вопросу



4\) level\_exam\_attempt\_module\_stats

\- агрегаты correct/total по модулям

\- CHECK: 0 <= correct\_cnt <= total\_cnt



\## Правило проекта

Имена constraints держим короче 63 символов (ограничение PostgreSQL).



