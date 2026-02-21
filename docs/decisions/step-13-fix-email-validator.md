\# Step-13 fix: email-validator для EmailStr



\## Что произошло

При использовании pydantic.EmailStr приложение падало на импорте:

ImportError: email-validator is not installed.



\## Решение

Добавлена runtime-зависимость email-validator, так как она обязательна для EmailStr.

Изменения зафиксированы в pyproject.toml и poetry.lock.



\## Почему так

\- Это устраняет падение приложения при старте/перезагрузке uvicorn.

\- Держит окружение воспроизводимым (Poetry lock).

