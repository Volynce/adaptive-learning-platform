\# Step-21: Допуск к level-exam (eligibility report)



\## Что сделано

1\) Реализован use-case get\_level\_exam\_eligibility():

\- собирает активную стадию пользователя

\- считает required/optional total/done

\- возвращает списки незакрытых required (minitest\_passed=false) и optional (is\_read=false)

\- вычисляет eligible=true только если все закрыто и required\_total>0



2\) Реализован endpoint:

\- GET /api/v1/progress/eligibility (protected)

Возвращает структурированный отчёт, пригодный как формализованный критерий допуска.



\## Зачем

\- Явно отделить “проверку допуска” от логики генерации экзамена.

\- Получить прозрачную диагностику причин недопуска (что именно не закрыто).

