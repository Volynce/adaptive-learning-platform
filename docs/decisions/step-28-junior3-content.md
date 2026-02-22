\# Step-28: Контент для Junior\_3 (seed + назначение через /content/assign) + e2e junior\_2 → junior\_3



\## Что сделано



1\) Подготовлен seed-скрипт для контента уровня Junior\_3  

Добавлен файл `scripts/seed/step-28-junior3-content.sql`.



В скрипте создаётся базовый набор статей для каждого модуля трека на `rank='junior'`, `level=3`:

\- \*\*optional\*\*: «Введение (module) — optional» (минимум `content\_optional\_per\_module` на модуль)

\- \*\*required\*\*: «Практика (module) — required» (отдельная статья-кандидат для weak-модулей)



Ключевое требование алгоритма назначения (Step-19/26):  

\*\*required для слабых модулей должен быть отдельной статьёй, не совпадающей с optional\*\*, поэтому на каждый `module\_id` нужно минимум 2 активных статьи (optional + required).



2\) Добавлены mini-test вопросы для required-статей Junior\_3  

В seed предусмотрена привязка мини-теста \*\*3/3\*\* к каждой required-статье через `article\_minitest\_questions`.



Это обеспечивает совместимость со Step-20: required-статьи обязаны иметь мини-тест (3 вопроса), а submit фиксирует `minitest\_passed=true`.



3\) Подтверждён сквозной сценарий перехода внутри ранга (junior\_2 → junior\_3)  

Проверено, что после выполнения условий допуска (eligibility=true) на Junior\_2:

\- `/exams/level/start` создаёт попытку и выдаёт 20 вопросов

\- `/exams/level/{attempt\_id}/submit` при PASS возвращает `progress.action="auto\_advanced"`

\- активная стадия автоматически переключается на Junior\_3 (level=3) транзакционно



4\) Проведена end-to-end проверка Junior\_3 до eligibility=true  

После auto-advance на Junior\_3:

\- `POST /content/assign` назначает optional + required

\- optional закрываются через `POST /content/{id}/read`

\- required закрываются через minitest `GET/POST /content/{id}/minitest(/submit)`

\- `GET /progress/eligibility` возвращает `eligible=true` для stage Junior\_3



\## Зачем



\- Поддержать непрерывный сквозной сценарий обучения внутри ранга junior (level 2 → level 3) без ручных правок БД.

\- Зафиксировать правило наполнения: \*\*на каждой стадии контент должен быть подготовлен заранее\*\*, иначе ломаются назначение контента и допуск к экзамену.

\- Разделить два типа данных:

&nbsp; - \*\*Seed/reference\*\* (articles + связи minitest) — воспроизводимость интеграционных прогонов.

&nbsp; - \*\*User-generated\*\* (назначения, чтение, результаты мини-тестов) — формируется через API в ходе использования.



\## Критерий готовности



\- В БД существуют статьи для `rank='junior'`, `level=3` по каждому модулю: минимум `optional + required`.

\- `POST /content/assign` на Junior\_3 возвращает успех (или 409 «уже назначено» при повторе), а не `MissingArticles`.

\- Для required статей доступен minitest (3 вопроса), а submit фиксирует `minitest\_passed=true`.

\- `GET /progress/eligibility` возвращает `eligible=true` для Junior\_3 после закрытия optional+required.

\- `POST /exams/level/{attempt\_id}/submit` на Junior\_2 при PASS возвращает `progress.action="auto\_advanced"` и активирует Junior\_3.



\## Артефакты



\- `scripts/seed/step-28-junior3-content.sql` — seed контента Junior\_3 (articles + minitest bindings)

\- `docs/decisions/step-28-junior3-content.md` — decision log шага (этот документ)

