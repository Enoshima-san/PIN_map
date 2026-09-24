# PIN_map

Веб-сервис с интерактивной картой для поиска нестандартных мест отдыха и прогулок

## Что реализовано

Django-модели создают 6 таблиц в PostgreSQL:

- **Location** - объекты (метки) на карте: парки, граффити, заброшенные места
- **Route** - прогулочные маршруты
- **RouteLocation** - связь маршрутов и объектов (какие точки входят и в каком порядке)
- **Media** - фото и видео, прикреплённые к объектам
- **Comment** - комментарии к объектам и маршрутам
- **Verification** - подтверждения объектов другими пользователями

Пользователи - во встроенной таблице Django `auth_user`

## Что нужно установить

Проверьте в терминале PowerShell, установлено ли:

```
python --version
psql --version
git --version
```
Если `psql` не распознаётся - это нормально. Напишите:
```
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" --version
```
Замените `18` на вашу версию.

Установите, если чего-то не хватает:

- **Python 3.10+** — https://www.python.org/downloads/ При установке поставьте галочку **«Add Python to PATH»**
- **PostgreSQL 14+** — https://www.postgresql.org/download/windows/ Запомните пароль пользователя `postgres`
- **Git** — https://git-scm.com/downloads

## Запуск проекта

### 1. Скачать проект

Используйте встроенный терминал PyCharm или VS Code

```
cd $env:USERPROFILE\Desktop
git clone https://github.com/Enoshima-san/PIN_map.git
cd PIN_map
```

На рабочем столе появится папка `PIN_map`

### 2. Создать и активировать виртуальное окружение

```
python -m venv venv
venv\Scripts\activate
```

После активации в начале строки появится `(venv)`

### 3. Установить зависимости

```
pip install -r requirements.txt
```

Установятся Django и другие библиотеки

### 4. Создать базу данных

Выполните (замените `18` на вашу версию PostgreSQL):

```
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

Введите пароль пользователя `postgres` (задавали при установке). Появится приглашение `postgres=#`

Создайте базу:
```
CREATE DATABASE my_django_db;
```

Проверьте:
```
\l
```

В списке должна быть `my_django_db`

Выйдите:
```
\q
```


### 5. Создать файл `.env` в корне проекта

Создайте новый файл с именем **`.env`** в корне проекта

Откройте его и впишите:

```
DB_NAME=my_django_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль_от_postgres
DB_HOST=localhost
DB_PORT=5432
```

Замените `ваш_пароль_от_postgres` на настоящий пароль от PostgreSQL. Сохраните файл


### 6. Создать таблицы в базе

```
python manage.py migrate
```

После выполнения этой команды в базе `my_django_db` появятся все 6 таблиц с префиксом `mapapp_`

## Проверка

Откройте pgAdmin (Win → начните печатать «pgAdmin»): `Servers` → `PostgreSQL 18` → `Databases` → `my_django_db` → `Schemas` → `public` → `Tables`

Должны быть таблицы:
- `mapapp_location`
- `mapapp_route`
- `mapapp_routelocation`
- `mapapp_media`
- `mapapp_comment`
- `mapapp_verification`

**Просмотр данных:** правой кнопкой по таблице → View/Edit Data → All Rows

**Структура таблицы:** правой кнопкой по таблице → Properties → вкладка Columns

Проект находится в активной разработке