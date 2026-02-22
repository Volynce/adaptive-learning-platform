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

