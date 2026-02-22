\# Step-27: Контент для Junior\_2 (seed + назначение через /content/assign)



\## Что сделано



1\) Подготовлен seed-скрипт контента для стадии Junior\_2 (rank='junior', level=2)



\- Добавлен файл: `scripts/seed/step-27-junior2-content.sql`.

\- Создаётся базовый набор статей по каждому модулю трека на `target\_rank='junior'`, `target\_level=2`:

&nbsp; - \*\*optional\*\*: «Введение (module) — optional» (минимум `content\_optional\_per\_module` на модуль).

&nbsp; - \*\*required-кандидат\*\*: «Практика (module) — required» (отдельная статья, чтобы алгоритм мог выбрать required отдельно от optional).



Ключевая цель — обеспечить инвариант назначения контента:

\- optional берётся по настройке `content\_optional\_per\_module`;

\- required для слабых модулей должен быть отдельной статьёй, не совпадающей с optional;

\- значит на модуль нужно минимум 2 статьи: optional + required-кандидат.



2\) Добавлены mini-test вопросы для required-статей Junior\_2



\- В seed предусмотрена привязка 3 вопросов к required-статьям через `article\_minitest\_questions`.

\- Это обеспечивает совместимость со Step-20: required-статьи должны иметь мини-тест \*\*3/3\*\*.



3\) Зафиксирован воспроизводимый способ применения seed на Docker Postgres



\- `psql -f` внутри `docker exec` ищет файл в контейнере.

\- Для файла на хосте используется stdin-редирект:



`docker exec -i alp\_postgres psql -U adaptive\_learning -d adaptive\_learning < scripts/seed/step-27-junior2-content.sql`



4\) End-to-end проверка сценария Junior\_2 до eligibility=true



\- `POST /api/v1/content/assign` на стадии Junior\_2 выполняется успешно (или 409 «уже назначено» при повторе).

\- optional отмечаются прочитанными через `POST /content/{id}/read`.

\- required закрываются мини-тестом 3/3 через `GET /content/{id}/minitest` + `POST /content/{id}/minitest/submit`.

\- `GET /api/v1/progress/eligibility` возвращает `eligible=true`.



\## Важное замечание (MVP-ограничение текущей реализации)



На первом прогоне выявлено, что текущая реализация назначения required в `content\_service` ожидает,

что required-кандидат распознаётся по маркеру в `title` («— required»). Поэтому статьи с суффиксом «— pool»

не воспринимались как кандидаты required и приводили к ошибке MissingArticles.



В Step-27 это решено данными (practice-статьи создаются/именуются как «— required»),

чтобы обеспечить сквозной прогон. В дальнейшем это следует заменить на явный признак (поле/enum),

а не эвристику по тексту заголовка.



\## Зачем



\- Поддержать непрерывный сквозной сценарий после Trainee\_0 → Junior\_1 → Junior\_2.

\- Обеспечить наличие контента на каждой стадии заранее, иначе ломается назначение и допуск.

\- Разделить seed/reference данные (контент, связи с вопросами) и user-generated данные (прочтение/мини-тесты).



\## Критерий готовности



\- В БД существуют статьи для `rank='junior', level=2` по каждому модулю трека (optional + required-кандидат).

\- `POST /api/v1/content/assign` на Junior\_2 не падает с MissingArticles.

\- Required статьи Junior\_2 имеют мини-тест 3 вопроса, submit фиксирует `minitest\_passed=true`.

\- `GET /api/v1/progress/eligibility` после закрытия required+optional возвращает `eligible=true`.



\## Артефакты



\- `scripts/seed/step-27-junior2-content.sql` — seed контента Junior\_2 (articles + minitest bindings).

\- `docs/decisions/step-27-junior2-content.md` — decision log шага.

