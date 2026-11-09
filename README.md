# Equipment Maintenance API (Лабораторная работа)
Микросервис для управления техническим обслуживанием и ремонтом (ТОиР) оборудования. Проект реализует RESTful API, взаимодействующее с реляционной базой данных, и включает веб-интерфейс для работы с данными.

## 🛠 Технологический стек
- Backend: Python 3.12, FastAPI, Uvicorn
- Database: PostgreSQL 17
- Database Admin: pgAdmin 4
- Frontend: HTML, CSS, Vanilla JS, Nginx (раздача статики)
- Infrastructure: Docker, Docker Compose (используется multi-stage сборка для API)

## 🚀 Быстрый запуск
Для запуска всех сервисов (API, БД, pgAdmin, Web) перейдите в корневую директорию проекта и выполните:

```bash
docker-compose up -d --build
```

### После запуска будут доступны следующие сервисы:
- Web-сайт (Frontend): http://localhost:8001
- REST API (Backend): http://localhost:8000
- Swagger UI (Документация API): http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (Логин: demo@example.com, Пароль: secret)

## 📁 Структура проекта
```text
.
├── api/                  # Исходный код бэкенда (FastAPI)
│   ├── components/       # Роутеры, схемы, основная логика
│   ├── db/               # Скрипты инициализации БД и модуль работы с БД
│   ├── Dockerfile        # Multi-stage Dockerfile для API
│   └── requirements.txt  # Python-зависимости
├── web/                  # Исходный код фронтенда
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── Dockerfile        # Dockerfile для Nginx
├── db_test/               
|   └── db_load.py        # Скрипт для заполнения базы тестовыми данными
└── docker-compose.yml    # Конфигурация всех контейнеров
```

## ⚙️ Настройки подключения к БД
Переменные окружения для подключения к PostgreSQL уже предустановлены в docker-compose.yml:
- Host: postgres
- Port: 5432
- User: postgres
- Password: postgres
- Database: equipment_maintenance

## 🧪 Тестирование и обработка ошибок
- Swagger: Вся документация по эндпоинтам (GET, POST, PATCH) автоматически сгенерирована и доступна по адресу /docs.
- Postman: Проект протестирован с помощью Postman.
- Обработка ошибок: Микросервис корректно обрабатывает некорректные данные (Pydantic валидация), возвращая HTTP-коды 400, 404, 409, 422 с понятными сопроводительными сообщениями, не прерывая работу приложения.