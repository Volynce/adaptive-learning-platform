\# Step-05: Docker Compose + PostgreSQL (dev-стенд)



\## Решения

1\) Dev-стенд базы данных поднимается через Docker Compose, чтобы любой git checkout был воспроизводим.

2\) Используем PostgreSQL (образ postgres:16-alpine).

3\) Порт проброшен на localhost:5432, так как backend пока запускается на хосте (не в контейнере).

4\) Данные сохраняются в docker volume (alp\_postgres\_data), чтобы база не терялась при перезапуске контейнера.

5\) Добавлен healthcheck (pg\_isready) для явной проверки готовности Postgres.

6\) Параметры контейнера согласуются с .env/.env.example через:

&nbsp;  POSTGRES\_USER, POSTGRES\_PASSWORD, POSTGRES\_DB и DATABASE\_URL.



\## Зачем

\- Разделить инфраструктуру (Postgres) и слой схемы (Alembic/DDL) по этапам для устойчивых откатов.

\- Сделать dev-окружение одинаковым на любой машине без ручной установки Postgres.



\## Критерий готовности

\- docker compose up -d поднимает контейнер alp\_postgres.

\- docker compose ps показывает статус healthy.

\- внутри контейнера выполняется SELECT 1.



