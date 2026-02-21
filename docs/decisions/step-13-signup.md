\# Step-13: DDL password\_hash + минимальный signup (email+password)



\## DDL

\- В таблицу users добавлено поле password\_hash (TEXT NOT NULL).

\- Пароль в чистом виде не хранится.



\## Код

\- Добавлен механизм хеширования пароля (bcrypt через passlib).

\- Реализован минимальный use-case регистрации:

&nbsp; - проверка уникальности email

&nbsp; - создание users с password\_hash

&nbsp; - попытка активировать стартовую стадию в user\_stage\_progress



\## Важное ограничение

Для полной регистрации с активацией прогресса требуются засиденные справочники:

tracks, stages, settings\_versions(status='active').

Если данных нет — endpoint возвращает 412 Precondition Failed (это ожидаемо до шага сидинга).



\## Критерий готовности

\- alembic upgrade head проходит, в users есть password\_hash.

\- POST /api/v1/auth/signup работает:

&nbsp; - 409 при повторном email,

&nbsp; - 412 если нет справочных данных,

&nbsp; - 201 после появления сидинга.

