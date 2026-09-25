# PiN — Социальная карта прогулок

Стек: **React + Leaflet** (frontend) · **GeoDjango + PostgreSQL/PostGIS + pgRouting** (backend) + **OSGeo4W  - GDAL, GEOS, PROJ** (библиотеки для картографии)

## Структура

```
pin-project/
├── backend/                 # Django / GeoDjango
│   ├── pin_project/         # settings (Задать Ваши параметры сервера PSQL и пути до установленных библиотек OSGeo4W), urls
│   ├── mapapp/              # models, views, serializers, admin
│   ├── manage.py
│   └── requirements.txt
└── frontend/                # Vite + React + react-leaflet
    ├── src/
    │   ├── App.jsx          # UI
    │   ├── api.js
    │   ├── main.jsx
    │   └── styles.css
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ с расширениями **PostGIS** и **pgRouting**

```sql
CREATE USER pin_user WITH PASSWORD 'pin_pass'; № Пропустить этап, если уже создан пользователь сервера PSQL
CREATE DATABASE pin_db OWNER pin_user; № Пропустить этап, если уже создана база данных проекта на сервере PSQL
\c pin_db
CREATE EXTENSION postgis;
CREATE EXTENSION pgrouting;
GRANT ALL ON SCHEMA public TO pin_user; № Указать своё имя пользователя сервера PSQL
```

## Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# переменные окружения (или defaults в settings.py)
export POSTGRES_DB=pin_db
export POSTGRES_USER=pin_user
export POSTGRES_PASSWORD=pin_pass
export POSTGRES_HOST=localhost

python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo          # демо-данные Новокузнецка
python manage.py createsuperuser    # опционально
python manage.py runserver
```

API: `http://127.0.0.1:8000/api/`

Основные эндпоинты:
- `GET/POST /api/items/` — каталог / создание
- `GET /api/items/?mine=1` — мои заявки
- `POST /api/items/{id}/verify/` — подтверждение
- `POST /api/items/{id}/approve|reject/` — модерация
- `POST /api/auth/` — login/register (`{"action":"login|register","email":"...","password":"..."}`)
- `GET /api/routing/shortest-path/?lat1=&lng1=&lat2=&lng2=` — пример pgRouting (нужна дорожная сеть)

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Откроется `http://localhost:5173` (проксирует `/api` на Django).

## pgRouting

Модель `RoadEdge` — заготовка таблицы рёбер. Для реальной маршрутизации:

1. Загрузить OSM-данные региона через [osm2pgrouting](https://github.com/pgRouting/osm2pgrouting)
2. Выполнить `SELECT pgr_createTopology('mapapp_roadedge', 0.0001, 'geom', 'id');`
3. Использовать эндпоинт `/api/routing/shortest-path/`

## Демо-аккаунты (после seed_demo)

| Email           | Пароль   | Роль      |
|-----------------|----------|-----------|
| admin@mail.ru   | admin123 | модератор |
| user1@mail.ru   | pass123  | пользователь     |

Клик по бейджу роли (email) в шапке переключает флаг модератора у текущего пользователя (для демо).
