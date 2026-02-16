\# Step-08: DDL для банка вопросов и контента (ручная миграция)



\## Что добавлено

1\) questions: вопросы, привязанные к modules.

&nbsp;  - CHECK: активный вопрос требует correct\_option\_id (is\_active=false OR correct\_option\_id IS NOT NULL).



2\) answer\_options: варианты ответа (pos=1..4).

&nbsp;  - CHECK pos 1..4.

&nbsp;  - UNIQUE (question\_id, pos) — позиция уникальна в рамках вопроса.

&nbsp;  - UNIQUE (question\_id, id) — техническое требование для композитного FK.



3\) Инвариант правильного ответа:

&nbsp;  - Композитный FK:

&nbsp;    (questions.id, questions.correct\_option\_id) -> (answer\_options.question\_id, answer\_options.id)

&nbsp;  Гарантия: correct\_option\_id принадлежит тому же вопросу.



4\) articles: статьи по модулям.

&nbsp;  - UNIQUE content\_ref (внешняя ссылка/идентификатор контента).



5\) user\_stage\_articles: назначение статей пользователю на стадии.

&nbsp;  - PK(user\_id, stage\_id, article\_id)

&nbsp;  - FK(user\_id, stage\_id) -> user\_stage\_progress (композитный)

&nbsp;  - CHECK kind in ('required','optional')

&nbsp;  - CHECK: required не может иметь read/read\_at

&nbsp;  - CHECK: optional не может иметь minitest\_passed/minitest\_passed\_at



6\) article\_minitest\_questions: мини-тест статьи (3 вопроса).

&nbsp;  - pos 1..3

&nbsp;  - UNIQUE(article\_id, question\_id)



\## Почему миграция ручная

Проект опирается на “жёсткие” инварианты БД (CHECK + композитные FK + уникальности), которые критичны для защиты домена от неконсистентных состояний и гонок.



\## Критерий готовности

\- alembic upgrade head проходит.

\- alembic current = 42c46d9f9aee (head).

\- Таблицы и ограничения проверены через psql (\\dt, \\d questions, \\d answer\_options).



