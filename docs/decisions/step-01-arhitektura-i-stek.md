Step-01: Архитектура и стек (зафиксированные решения)



Проект: adaptive-learning-platform

Репозиторий: https://github.com/Volynce/adaptive-learning-platform



Владелец: Volynce



1\) Архитектура системы (целевое состояние)



Backend: единый доменный сервис (модульный монолит).



База данных: PostgreSQL как единственный источник истины (ограничения + транзакции обеспечивают инварианты).



Клиент (цель): Web SPA (браузер). Текущая фаза: API-first (Swagger/Postman + тесты).



Фоновые задачи: опционально позже; на MVP допускаются синхронные use-case сценарии.



2\) Слойность backend (обязательное правило)



Слои:



API (роутеры FastAPI): только транспорт (валидация, auth middleware, HTTP-маппинг).



Application (use-cases): границы транзакций + оркестрация сценариев.



Domain (правила/адаптивность): чистые бизнес-правила, без HTTP/ORM.



Infrastructure (БД/безопасность): репозитории SQLAlchemy/psycopg, миграции, утилиты JWT/паролей.



Правила зависимостей:



api -> application (разрешено), api -> infrastructure (прямой доступ к БД запрещён).



application -> domain + infrastructure (через UoW/репозитории).



domain не должен зависеть от api или infrastructure.



infrastructure не должен содержать бизнес-правил.



3\) Доменные модули (bounded contexts)



Идентификация и авторизация (users/admin\_users, хеш пароля, JWT)



Каталог (tracks/stages/modules; сидинг справочников)



Версионирование настроек (settings\_versions/track\_settings; фиксация settings\_version\_id на стадии пользователя)



Прогресс (user\_stage\_progress: active/pending\_approval/completed)



Контент (articles/user\_stage\_articles/article\_minitest\_questions)



Диагностика (diagnostika\_\*; строго один раз на пользователя)



Экзамен уровня (level\_exam\_\*; попытки до PASS; после PASS пересдача заблокирована)



Финал ранга (rank\_final\_\*; попытки до PASS; после PASS пересдача заблокирована)



Движок адаптивности (выбор K слабых модулей, распределение min/max, без дублей вопросов внутри попытки)



Подтверждения (approval\_requests; approve переходов и выпуск/graduate)



4\) Политика конфигурации (env)



Источник истины конфигурации: переменные окружения.



Локальная разработка использует .env (НЕ коммитится). В репозитории хранится .env.example (коммитится).



Подключение к БД задаётся ТОЛЬКО через DATABASE\_URL.



Все настройки читаются через типизированный Settings (pydantic-settings), а не через разрозненные обращения к os.environ.



Минимальный набор ключей окружения:



APP\_ENV, APP\_DEBUG



DATABASE\_URL



JWT\_SECRET, JWT\_ALG, JWT\_ACCESS\_TTL\_MINUTES



параметры хеширования паролей (алгоритм/стоимость)



5\) Точки входа FastAPI и версионирование API



Единая фабрика приложения: create\_app() в main.py; экспорт: app = create\_app()



Маршруты публикуются под /api/v1 (версионированный контракт).



Централизованная сборка роутеров: api/router.py + api/v1/router.py (подключение модульных роутеров).



Зависимости централизованы в api/deps.py (db session, current\_user/admin).



Доменные ошибки отделены от HTTP-маппинга (domain/errors.py vs api/errors.py).



Запрещено выполнять миграции/сидинг/DDL при старте приложения.



6\) Доступ к БД и миграции



Доступ к БД: синхронный SQLAlchemy 2.0 + psycopg (приоритет — транзакционная дисциплина).



Эволюция схемы: Alembic — единственный источник истины DDL.



Миграции Alembic: только ручные (запрещён --autogenerate).



Каждая миграция = один логический change-set; осмысленное имя; downgrade обязателен.



Инварианты PostgreSQL (partial unique, CHECK, составные FK) версионируются явно в миграциях.



7\) Авторизация (dev/MVP)



Email + пароль.



JWT только access-токен (Authorization: Bearer <token>).



Дальнейшее усложнение (refresh/cookies) должно локализоваться в auth-подсистеме; доменные эндпоинты остаются стабильными.



8\) Локальная инфраструктура



Docker Compose для воспроизводимого dev-стенда (минимум: контейнер PostgreSQL).



Цель: любой git checkout должен запускаться с одинаковыми соглашениями env+compose.

