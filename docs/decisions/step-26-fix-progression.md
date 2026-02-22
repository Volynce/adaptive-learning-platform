\# Step-26-fix: Уточнение progression\_service для ранговой прогрессии



\## Причина фикса

После базовой фиксации Step-26 обнаружено, что логика прогрессии после PASS level-exam должна

поддерживать:

\- Trainee\_0 -> Junior\_1 только через pending\_approval,

\- auto-advance внутри ранга (level 1->2, 2->3),

\- завершение ранга (level=3) через pending\_approval для перехода Middle/Senior и отдельный сценарий graduation.



\## Что изменено

1\) ProgressAction.action нормализован под API-контракт:

\- none

\- auto\_advanced

\- pending\_approval

2\) Вынесены вспомогательные функции:

\- \_get\_stage\_meta()

\- \_find\_stage\_id()

3\) Добавлена ветка rank-level=3:

\- junior\_3 -> middle\_1 (approval)

\- middle\_3 -> senior\_1 (approval)

\- senior\_3 -> graduation (approval type=graduation)

4\) Важное архитектурное правило:

apply\_progress\_after\_level\_exam\_pass() остаётся транзакционной функцией (без commit/rollback),

вызывается внутри submit\_level\_exam().



\## Риски/заметки

\- Идемпотентность вставки approval\_requests и user\_stage\_progress должна контролироваться инвариантами БД.

\- Повторный вызов прогрессии теоретически может упасть по уникальным ограничениям; это допустимо в учебной версии,

но при необходимости будет усилено ON CONFLICT / rowcount проверками.



End-to-end проверка ранговой прогрессии (junior\_1 → junior\_2)



Контекст:



Пользователь: seedtest3@example.com



Активная стадия до экзамена: stage\_id=2 (junior\_1), status=active.



Проверка:



Выполнен старт экзамена: POST /api/v1/exams/level/start

Получено: attempt\_id=3, total\_q=20.



Выполнен submit с корректными ответами (selected\_option\_id = correct\_option\_id для каждого question\_id):

POST /api/v1/exams/level/3/submit

Результат:



passed=true



progress.action="auto\_advanced"



progress.from\_stage\_id=2



progress.to\_stage\_id=3



Проверка текущей стадии после submit:

GET /api/v1/progress/current-stage

Результат: stage\_id=3 (junior\_2), status=active.



Проверка в БД:



user\_stage\_progress(stage\_id=2) -> completed, completed\_at заполнен



user\_stage\_progress(stage\_id=3) -> active, activated\_at заполнен



Вывод:



Транзакционная автопрогрессия внутри ранга работает корректно: PASS level-exam на level=1/2 активирует следующий level без участия админа.

