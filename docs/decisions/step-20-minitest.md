\# Step-20: Мини-тест 3/3 для required статей



\## Что сделано

1\) Seed mini-тестов: article\_minitest\_questions (3 вопроса на статью).

2\) Use-case get\_minitest(): выдаёт 3 вопроса и варианты (только для required).

3\) Use-case submit\_minitest(): PASS только при 3/3; ставит user\_stage\_articles.minitest\_passed=true.

4\) API:

\- GET  /api/v1/content/{article\_id}/minitest

\- POST /api/v1/content/{article\_id}/minitest/submit



\## Правила

\- Мини-тест доступен только для required статей, назначенных пользователю на текущей стадии.

\- История попыток мини-теста не хранится; хранится только факт PASS.

\- После PASS флаг minitest\_passed не сбрасывается.



\## Критерий готовности

\- minitest GET возвращает 3 вопроса

\- submit возвращает passed=true при 3/3 и фиксирует minitest\_passed=true

