\# Step-12: Инфраструктура БД в приложении (engine/session + health/db)



\## Решения

1\) Подключение к БД выполняется через SQLAlchemy 2.0 (sync) с использованием DATABASE\_URL из Settings.

2\) Engine и sessionmaker создаются лениво (через cache), чтобы импорты модулей были безопасны.

3\) Для FastAPI добавлен dependency get\_db(), выдающий Session и гарантирующий закрытие.

4\) Добавлен технический endpoint /api/v1/health/db, который выполняет SELECT 1 и подтверждает связку API ↔ Postgres.



\## Зачем

\- Получить устойчивую инфраструктурную основу перед внедрением use-case сценариев и транзакций.

\- Сохранить слоистую архитектуру: инфраструктура БД отдельно от домена и API-логики.



\## Критерий готовности

\- docker compose ps: Postgres healthy.

\- uvicorn запускается.

\- GET /api/v1/health/db возвращает {"status":"ok","db":"ok"}.

