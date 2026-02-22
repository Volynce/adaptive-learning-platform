\# Step-29: Переход junior\_3 → middle\_1 через approvals (boundary rank)



\## Что сделано



1\) Зафиксирован доменный сценарий «граница ранга» после PASS level-exam на junior\_3:

\- при успешном сабмите level-exam на стадии rank='junior', level=3 система \*\*не активирует\*\* следующую стадию автоматически;

\- вместо этого стадия переводится в `pending\_approval`, а переход оформляется через `approval\_requests`.



2\) End-to-end прогон на пользователе `seedtest3@example.com`:

\- подтверждён допуск `GET /api/v1/progress/eligibility -> eligible=true` на junior\_3;

\- выполнен `POST /api/v1/exams/level/start` и `POST /api/v1/exams/level/{attempt\_id}/submit` (PASS);

\- в ответе submit проверено поле `progress`:

&nbsp; - `action="pending\_approval"`

&nbsp; - `from\_stage\_id=<junior\_3>`

&nbsp; - `to\_stage\_id=<middle\_1>`



3\) Проверка на уровне БД:

\- `user\_stage\_progress` для stage junior\_3 установлен в `status='pending\_approval'` с `completed\_at`;

\- создана запись в `approval\_requests`:

&nbsp; - `type='rank\_transition'`

&nbsp; - `status='pending'`

&nbsp; - `from\_stage\_id=junior\_3`

&nbsp; - `to\_stage\_id=middle\_1`



4\) Админский контур подтверждения:

\- `POST /api/v1/admin/login` выдаёт access JWT со `scope=admin`;

\- `GET /api/v1/admin/approvals/pending` возвращает список ожидающих заявок;

\- `POST /api/v1/admin/approvals/{id}/approve` переводит заявку в `approved` и \*\*активирует\*\* `middle\_1` для пользователя.



\## Зачем



\- Развести два типа прогрессии:

&nbsp; 1) Внутри ранга (level 1→2→3) — автоматическая прогрессия (`auto\_advanced`).

&nbsp; 2) Между рангами (junior→middle→senior) — только через управляемое подтверждение (approval), чтобы обеспечить контроль качества и управляемость траектории.



\- Зафиксировать транзакционную дисциплину: PASS экзамена и создание approval выполняются в одной доменной операции, не оставляя систему в «полупереходном» состоянии.



\## Критерий готовности



\- PASS level-exam на junior\_3 возвращает `progress.action="pending\_approval"` и создаёт `approval\_requests(status='pending')`.

\- До approve у пользователя активная стадия \*\*не\*\* меняется на middle\_1 (она становится `pending\_approval`).

\- После admin approve:

&nbsp; - заявка `approval\_requests` становится `approved`;

&nbsp; - `middle\_1` появляется/активируется в `user\_stage\_progress` как `status='active'`;

&nbsp; - `GET /api/v1/progress/current-stage` показывает `rank='middle', level=1`.



\## Артефакты



\- docs/decisions/step-29-junior3-to-middle1-approval.md — описание шага и критерии готовности.

