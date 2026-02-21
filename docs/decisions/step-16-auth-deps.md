\# Step-16: Централизация JWT dependencies (current\_user)



\## Что сделано

1\) В api/deps.py добавлены:

\- current\_user\_id: извлечение user\_id из Bearer access JWT

\- current\_user: загрузка профиля пользователя из БД по user\_id



2\) users/me упрощён: использует единый dependency current\_user.



\## Зачем

\- Исключить дублирование логики проверки токена в роутерах.

\- Зафиксировать единые правила 401/404 и валидации payload (type=access, sub=int).

\- Подготовить базу для защиты будущих эндпоинтов diagnostika/content/exams/approvals.



\## Критерий готовности

\- /auth/login выдаёт access\_token

\- /users/me возвращает профиль при валидном токене

\- /users/me возвращает 401 без токена

