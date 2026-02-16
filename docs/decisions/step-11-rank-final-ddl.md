\# Step-11: DDL финального экзамена ранга (rank\_final\_\*)



\## Что добавлено

1\) rank\_final\_attempts

\- UNIQUE(user\_id, stage\_id, attempt\_no)

\- partial UNIQUE(user\_id, stage\_id) WHERE passed=true (PASS фиксируется один раз)

\- CHECK: attempt\_no>=1, score\_total>=0, passed=>passed\_at not null



2\) rank\_final\_attempt\_questions

\- PK(attempt\_id, question\_id) запрещает повторы вопросов внутри попытки



3\) rank\_final\_attempt\_answers

\- FK на attempt\_questions: нельзя ответить на вопрос, которого не было в попытке

\- композитный FK(question\_id, selected\_option\_id) -> answer\_options(question\_id, id)



4\) rank\_final\_attempt\_module\_stats

\- CHECK: 0 <= correct\_cnt <= total\_cnt



\## Правило проекта

Имена constraints держим короче 63 символов (ограничение PostgreSQL).



