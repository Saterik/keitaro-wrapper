# Keitaro Campaign Manager

Обёртка над Keitaro Admin API для создания и управления кампаниями с geo-based потоками.

## Возможности

### 🎯 Создаватор кампаний
- Принимает: название, ISO-код страны (RU, US, DE...), ID оффера в Keitaro
- Автоматически создаёт кампанию с **двумя потоками**:
  1. **Гео-фильтр** — ловит трафик из указанной страны → редирект на Google
  2. **Оффер** — весь остальной трафик уходит на выбранный оффер
- Настраивает домен, группу, источник трафика (авто-выбор первого доступного)
- Префикс названия: `test_ivanov_` (настраивается)

### 📝 Редактор кампаний
- Список всех кампаний с ключевыми данными
- Просмотр деталей: стримы, офферы, настройки
- **Добавление офферов** в существующую кампанию (обновляет стрим 2 в Keitaro)
- **Удаление офферов** из кампании
- **Удаление кампании** (удаляется и из Keitaro)

## Стек
- **Backend**: FastAPI, SQLAlchemy 2.0, SQLite, httpx
- **Frontend**: Vanilla HTML/CSS/JS (без сборки)
- **API**: Keitaro Admin API

---

## Быстрый старт

### 1. Требования
- Python 3.10+
- Keitaro с доступом к Admin API
- **Admin API Key** (создаётся в Keitaro: Profile → API Keys → New Key → Admin permissions)

### 2. Установка

```bash
cd keitaro-wrapper/backend

# Виртуальное окружение
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Зависимости
pip install -r requirements.txt
```

### 3. Конфигурация

Скопируйте и отредактируйте `.env`:

```bash
cp .env.example .env
```

```env
# ОБЯЗАТЕЛЬНО: ваш Admin API Key из Keitaro
KEITARO_API_URL=https://tlgk.host
KEITARO_API_KEY=ваш_админ_апи_ключ

# База (SQLite по умолчанию)
DATABASE_URL=sqlite:///./keitaro_wrapper.db

# Сервер
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# Префикс кампаний
CAMPAIGN_PREFIX=test_ivanov_
```

> ⚠️ **Важно**: Пароль `T9*2jiT8zoUKEH1J7VvFqkXM` — это пароль от админки. Для API нужен отдельный **Admin API Key**, который создаётся в профиле Keitaro.

### 4. Запуск

```bash
python main.py
```

Откройте **http://localhost:8000**

---

## Структура проекта

```
keitaro-wrapper/
├── backend/
│   ├── main.py              # FastAPI приложение
│   ├── config.py            # Настройки (Pydantic Settings)
│   ├── database.py          # SQLAlchemy engine/session
│   ├── models.py            # ORM модели (Campaign, CampaignOffer)
│   ├── schemas.py           # Pydantic схемы валидации
│   ├── keitaro_client.py    # Асинхронный клиент Keitaro API
│   ├── services/
│   │   └── campaign_service.py  # Бизнес-логика
│   ├── api/
│   │   └── campaigns.py     # REST эндпоинты
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # Ваши секреты (не в git!)
├── frontend/
│   ├── index.html           # Разметка
│   ├── styles.css           # Стили
│   └── app.js               # Логика UI
└── README.md
```

---

## API Endpoints

### Кампании
| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/campaigns` | Создать кампанию |
| `GET` | `/api/campaigns` | Список кампаний |
| `GET` | `/api/campaigns/{id}` | Детали кампании + офферы |
| `PUT` | `/api/campaigns/{id}` | Обновить настройки |
| `DELETE` | `/api/campaigns/{id}` | Удалить кампанию |

### Офферы в кампании
| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/campaigns/{id}/offers` | Добавить оффер |
| `DELETE` | `/api/campaigns/{id}/offers/{offer_id}` | Удалить оффер |
| `GET` | `/api/campaigns/{id}/offers` | Список офферов кампании |

### Справочники (для UI)
| Метод | Путь |
|-------|------|
| `GET` | `/api/campaigns/resources/offers` |
| `GET` | `/api/campaigns/resources/domains` |
| `GET` | `/api/campaigns/resources/groups` |
| `GET` | `/api/campaigns/resources/traffic-sources` |

### Системные
| Метод | Путь |
|-------|------|
| `GET` | `/health` |
| `GET` | `/docs` — Swagger UI |
| `GET` | `/redoc` — ReDoc |

---

## Логика создания кампании

При `POST /api/campaigns`:

1. **Создаёт кампанию в Keitarо**:
   - `name: "{prefix}{name}"` (напр. `test_ivanov_summer_sale`)
   - `state: enabled`
   - `cost_type: CPC`, `cost_auto: true`
   - `bind_visitors: true`
   - domain/group/source — переданные или первый доступный

2. **Стрим 1 (позиция 1)** — Geo Filter → Google:
   - `type: regular`, `action_type: redirect`, `schema: redirect`
   - `action_options: {url: "https://www.google.com", redirect_type: "302"}`
   - Фильтр: `country IN [geo_code]`

3. **Стрим 2 (позиция 2)** — Offer:
   - `type: regular`, `action_type: offer`, `schema: offer`
   - `offers: [{offer_id: <переданный>, weight: 100}]`
   - Без фильтров (ловит остальной трафик)

4. **Сохраняет в локальную БД** для управления офферами.

---

## Добавление оффера в существующую кампанию

1. Берёт текущий **стрим 2** из Keitaro
2. Дописывает новый оффер в `offers[]`
3. `PUT /streams/{stream_id}` с обновлённым массивом
4. Записывает связь в локальную БД (`campaign_offers`)

---

## Разработка

### Автозагрузка
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Миграции (Alembic)
```bash
alembic init migrations
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

## Продакшн

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY frontend/ ./frontend/
EXPOSE 8000
CMD ["python", "backend/main.py"]
```

### Переменные окружения
```env
KEITARO_API_URL=https://your-keitaro.com
KEITARO_API_KEY=prod_key
DATABASE_URL=postgresql://user:pass@host/db
DEBUG=false
```

---

## Troubleshooting

| Проблема | Решение |
|----------|---------|
| `401 Unauthorized` на ресурсах | Проверьте `KEITARO_API_KEY` в `.env` — нужен **Admin API Key**, не пароль |
| Не создаётся кампания | Проверьте, что в Keitaro есть хотя бы 1 домен, 1 группа, 1 источник трафика |
| Ошибка валидации офферов | Схема `KeitaroOffer` ожидает `country` как строку или массив — уже исправлено |
| Фронтенд не грузится | Убедитесь, что `backend/main.py` отдаёт статику из `../frontend` (не `dist`) |

---

## Лицензия

MIT — используйте свободно.