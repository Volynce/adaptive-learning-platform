\# Step-23: submit level-exam attempt + scoring + module stats



\## Что сделано

1\) Реализован submit попытки level-exam:

\- принимает ответы на все вопросы попытки

\- записывает level\_exam\_attempt\_answers

\- считает score\_total

\- формирует level\_exam\_attempt\_module\_stats

\- фиксирует passed=true/passed\_at при score\_total >= pass\_score (из track\_settings)



2\) Инварианты

\- нельзя отвечать на вопросы вне попытки (FK attempt\_answers -> attempt\_questions)

\- нельзя сабмитить чужую попытку

\- нельзя сабмитить попытку после PASS (409)

\- требуется полный набор ответов (20/20) для воспроизводимости стенда



\## Проверка

\- авто-сабмит через correct\_option\_id дал passed=true, score\_total=20

\- module\_stats суммируются до total=20, correct=20

