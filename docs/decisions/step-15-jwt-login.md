\# Step-15: JWT login (access-only) + защита эндпоинтов



\## Что сделано

1\) Добавлен выпуск access JWT (python-jose\[cryptography]).

2\) Реализован endpoint POST /api/v1/auth/login (email+password → access\_token).

3\) Реализована проверка Bearer токена через dependency current\_user\_id.

4\) Добавлен защищённый endpoint GET /api/v1/users/me.



\## Правила

\- Только access JWT (без refresh) для учебного стенда.

\- JWT параметры берутся из Settings/env: JWT\_SECRET, JWT\_ALG, JWT\_ACCESS\_TTL\_MINUTES.

\- Защита эндпоинтов выполняется через FastAPI dependency, а не вручную в каждом роуте.



\## Критерий готовности

\- login возвращает access\_token

\- /users/me возвращает данные пользователя при валидном токене и 401 при отсутствии/ошибке

