\# Step-24: Автоматическая прогрессия после PASS level-exam (в одной транзакции)



\## Что сделано

1\) В submit\_level\_exam() добавлен доменный шаг прогрессии, выполняемый только при passed=true.

2\) Логика прогрессии вынесена в отдельный use-case: progression\_service.apply\_progress\_after\_level\_exam\_pass().



\## Правила

\- Junior/Middle/Senior: при PASS на level 1 или 2 выполняется auto-advance на следующую стадию того же rank (level+1).

&nbsp; - Текущая стадия: status=completed, completed\_at=now()

&nbsp; - Следующая стадия: создаётся/активируется status=active, activated\_at фиксируется

\- Trainee\_0: при PASS выполняется переход в pending\_approval и создаётся approval\_request(type=rank\_transition, status=pending) на переход к Junior\_1.

\- Level=3: прогрессия после level-exam не выполняется (дальнейший шаг домена — rank-final).



\## Почему так

\- Прогрессия является частью доменного перехода состояния и должна быть атомарна с фиксацией PASSED.

\- Разделение сервисов (exams vs progression) сохраняет модульность и снижает риск конфликтов при расширении домена.



\## Проверка

\- На новом пользователе: PASS level-exam → progress.action=pending\_approval и создан approval\_request.

