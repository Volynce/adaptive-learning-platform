\# Step-26: Rank progression (Junior\_1) — контент и допуск к level-exam



Проект: adaptive-learning-platform  

Ветка: step-26-rank-progression



\## Цель шага

Обеспечить прохождение полного цикла на стадии Junior\_1 (rank=junior, level=1):

назначение контента → закрытие optional (read) → закрытие required (minitest 3/3) → формирование допуска к level-exam через eligibility отчёт.



\## Что было сделано

1\) Снято MVP-ограничение "assign только для Trainee\_0":

&nbsp;  - Назначение контента теперь поддерживает любую активную стадию пользователя (rank/level берутся из stages).

2\) Уточнена логика выбора статей:

&nbsp;  - optional и required различаются по признаку в title (MVP-правило сидирования: "... — optional/required").

&nbsp;  - optional выдаётся всем модулям трека в количестве content\_optional\_per\_module на модуль.

&nbsp;  - required выдаётся для K слабых модулей (content\_k\_weak\_modules), слабость считается как errors = total\_cnt - correct\_cnt по diagnostika\_module\_stats.

3\) Добавлен/использован seed контента для junior\_1:

&nbsp;  - статьи articles(target\_rank='junior', target\_level=1)

&nbsp;  - minitest (article\_minitest\_questions) для required статей



\## Проверка (end-to-end, пользователь seedtest3@example.com)

\- /api/v1/content/assign → контент присутствует (повторное назначение запрещено, возвращает AlreadyAssigned)

\- /api/v1/content/my → получены OPT\_IDS и REQ\_IDS на stage\_id=2

\- /api/v1/content/{id}/read (optional) → HTTP 204

\- /api/v1/content/{id}/minitest/submit (required) → passed=true, correct\_cnt=3/3

\- /api/v1/progress/eligibility → eligible=true (required\_done=required\_total, optional\_done=optional\_total)



\## Принятые правила и инварианты

\- Контент назначается один раз на стадию (защита от повторного assign).

\- Optional закрывается только read (is\_read), Required закрывается только minitest\_passed.

\- Допуск к level-exam определяется через агрегированный отчёт eligibility и не “вычисляется на глаз” в роутере.



\## Риски и ограничения (осознанно в MVP)

\- Разделение optional/required реализовано через title (строковый признак). В прод-версии это лучше заменить явным типом статьи (например, поле kind в articles или отдельная таблица правил назначения).

\- Адаптивность контента пока rule-based (по diagnostika), без ML.



\## Результат шага

Стадия Junior\_1 поддерживает назначение контента и достижение eligibility=true, что позволяет переходить к запуску и сдаче level-exam на уровне Junior.

