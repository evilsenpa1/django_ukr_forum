# Ukr-Forum

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://github.com/evilsenpa1/django_ukr_forum/actions/workflows/django.yml/badge.svg)](https://github.com/evilsenpa1/django_ukr_forum/actions)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)

> 🇬🇧 English | [🇺🇦 Українська](#ukr-forum-1)

A Ukrainian community platform combining a marketplace with geolocation search, user profiles with a referral tracking system, and a geographic location hierarchy. Created to help ukrainians.

**Production:** [ukrkolo.site](https://ukrkolo.site)

> _Migrated from a private repository — pre-migration commit history is not preserved. Active development continues in this repo going forward._

---

## Features

- **Product marketplace** — create, browse, and filter listings by category, status (new/used), and location
- **Geo-radius search** — find products within a custom radius using the Haversine formula
- **Geographic hierarchy** — Country → Region → City → LocationPlace, with Ukrainian name translations and flag emojis
- **Referral system** — invite users via unique hashids-encoded referral codes with recursive tree tracking
- **User profiles** — granular privacy controls (phone, email, location, social links visible/hidden per field)
- **Redis caching** — category/product caches invalidated automatically via Django signals
- **Custom middleware** — `LoginRequiredMiddleware` for site-wide auth enforcement; `VisitorTrackingMiddleware` for page view analytics
- **Image uploads** — up to 10 images per product with server-side validation (size, dimensions, aspect ratio, file type)
- **GDPR consent** — versioned consent texts with stored consent date per user

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2, Python 3.12 |
| Database | PostgreSQL 16 |
| Cache / Sessions | Redis 7 + django-redis |
| Frontend | Tailwind CSS 4 (Node 18 watcher) + django-widget-tweaks |
| Web server | Gunicorn (gthread) + Nginx |
| Containerization | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Security scanning | pip-audit, gitleaks, Semgrep (SAST), OWASP ZAP, Nikto |

---

## Project Structure

```
config/     — Settings, root URLs, WSGI/ASGI, custom middleware
main/       — Homepage, visitor tracking, breadcrumbs, context processors
users/      — CustomUser model, auth, referral system
shop/       — Product catalog, categories, images, filtering, geo-radius search
geo/        — Country/Region/City/LocationPlace hierarchy
core/       — Shared mixins (AuthorOrStaffRequiredMixin), permission utils, encoding helpers
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose — recommended
- Or: Python 3.12+, PostgreSQL 16, Redis 7, Node 18 (for Tailwind)

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your values (see Environment Variables section below)
```

### Run with Docker (recommended)

```bash
docker-compose -f docker-compose.dev.yml up
```

Services started:
- Django dev server → `http://localhost:8000`
- PostgreSQL 16 → `localhost:5433`
- Redis → `localhost:6379`
- Tailwind CSS watcher (auto-recompiles on template changes)

### Run without Docker

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Create a superuser

```bash
python manage.py createsuperuser
```

---

## Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Production stack:
- Gunicorn (3 workers, gthread, max 1000 req/worker)
- Nginx reverse proxy with SSL termination
- Certbot for automatic Let's Encrypt certificate renewal

Pre-deploy validation:

```bash
python manage.py check --deploy
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` | PostgreSQL credentials |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | Redis connection |
| `HASHIDS_SALT` | Salt for referral code encoding |
| `COUNTRY_STATE_CITY_API_KEY` | [CountryStateCity API](https://countrystatecity.in/) key for geo data |
| `GEO_API_KEY` | Google Maps API key |
| `TIME_ZONE` | Django timezone (default: `UTC`) |
| `LANGUAGE_CODE` | Django language (default: `uk`) |

See `.env.example` for a full template.

---

## Running Tests

```bash
# All tests
python manage.py test shop.tests --verbosity=2

# Single test class
python manage.py test shop.tests.test_views.CreateProductViewTest

# With coverage report
coverage run --source='shop' manage.py test shop.tests
coverage report

# Faster runs (parallel + reuse DB)
python manage.py test shop.tests --parallel --keepdb
```

Tests live in `shop/tests/` — `test_views.py`, `test_views_advanced.py`, `test_factories.py`.  
Coverage includes access-control tests, form validation, geo-search, and cache isolation via `DummyCache`.

---

## CI/CD Pipeline

GitHub Actions pipeline triggers on pushes to `main`/`develop` and all PRs.

| Job | What it does |
|-----|-------------|
| **Django** | System check, migration validation, test suite with coverage |
| **Security (static)** | `pip-audit` (dependency vulns), `gitleaks` (secrets scan), Semgrep SAST (Django ruleset), `--deploy` check |
| **Security (dynamic)** | Spins up full Nginx + Gunicorn stack; runs OWASP ZAP baseline scan + brute-force rate-limit test (expects HTTP 429) |
| **Penetration testing** | Nikto web scanner against the running stack |

---

## Key Design Decisions

### Haversine geo-radius search
Products can be searched within a radius (km) of a city. The distance is calculated server-side using the Haversine formula on city latitude/longitude stored in the `geo_city` table.

### Referral system
`UserReferrals` stores referral relationships. Each code is generated with `hashids` encoding of the primary key, making codes short and non-guessable. The referral tree is traversed recursively — deep chains (100+ levels) risk `RecursionError`.

### Redis cache invalidation
Django signals (`post_save`, `post_delete`) on `Product` and `Categories` models trigger cache key deletion, keeping cached listings fresh without a TTL flush.

### LoginRequiredMiddleware
All URLs require authentication except: `/`, `/users/login/`, `/users/signup/`, `/.well-known/`, `/health/`.


## Author

Oleksii U.
https://github.com/evilsenpa1

---

---

> 🇺🇦 Нижче — версія цього README українською мовою.

---

# Ukr-Forum

Українська спільнотна платформа, що поєднує маркетплейс з пошуком за геолокацією, профілі користувачів із системою реферального відстеження та ієрархію географічних локацій. Створена, щоб допомагати українцям.

**Production:** [ukrkolo.site](https://ukrkolo.site)

> _Перенесено з приватного репозиторію — історія комітів до міграції не збережена. Подальша розробка ведеться тут._

---

## Можливості

- **Маркетплейс** — створення, перегляд та фільтрація оголошень за категорією, статусом (нове/вживане) і локацією
- **Пошук за радіусом** — пошук товарів у заданому радіусі (км) за формулою Гаверсинуса
- **Географічна ієрархія** — Країна → Регіон → Місто → Місце, з перекладами назв українською та емодзі прапорів
- **Реферальна система** — запрошення користувачів через унікальні коди на основі hashids із рекурсивним відстеженням дерева
- **Профілі користувачів** — гнучкі налаштування приватності (телефон, email, локація, соцмережі — видимість кожного поля окремо)
- **Кешування Redis** — кеш категорій та товарів автоматично інвалідується через Django signals
- **Кастомний middleware** — `LoginRequiredMiddleware` для обов'язкової авторизації на всьому сайті; `VisitorTrackingMiddleware` для аналітики перегляду сторінок
- **Завантаження зображень** — до 10 фото на товар із серверною валідацією (розмір, розміри, пропорції, тип файлу)
- **Згода GDPR** — версіоновані тексти згоди із збереженням дати підписання для кожного користувача

---

## Технічний стек

| Рівень | Технологія |
|--------|-----------|
| Backend | Django 5.2, Python 3.12 |
| База даних | PostgreSQL 16 |
| Кеш / Сесії | Redis 7 + django-redis |
| Frontend | Tailwind CSS 4 (Node 18 watcher) + django-widget-tweaks |
| Вебсервер | Gunicorn (gthread) + Nginx |
| Контейнеризація | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Сканування безпеки | pip-audit, gitleaks, Semgrep (SAST), OWASP ZAP, Nikto |

---

## Структура проєкту

```
config/     — Налаштування, кореневі URL, WSGI/ASGI, кастомний middleware
main/       — Головна сторінка, відстеження відвідувачів, хлібні крихти, контекст-процесори
users/      — Модель CustomUser, авторизація, реферальна система
shop/       — Каталог товарів, категорії, зображення, фільтрація, пошук за геолокацією
geo/        — Ієрархія Країна/Регіон/Місто/Місце
core/       — Спільні міксини (AuthorOrStaffRequiredMixin), утиліти прав доступу, хелпери кодування
```

---

## Початок роботи

### Вимоги

- Docker & Docker Compose — рекомендовано
- Або: Python 3.12+, PostgreSQL 16, Redis 7, Node 18 (для Tailwind)

### Налаштування середовища

```bash
cp .env.example .env
# Відредагуйте .env зі своїми значеннями (дивіться розділ "Змінні середовища" нижче)
```

### Запуск через Docker (рекомендовано)

```bash
docker-compose -f docker-compose.dev.yml up
```

Запущені сервіси:
- Django dev server → `http://localhost:8000`
- PostgreSQL 16 → `localhost:5433`
- Redis → `localhost:6379`
- Tailwind CSS watcher (автоматично перекомпілює при змінах у шаблонах)

### Запуск без Docker

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Створення суперкористувача

```bash
python manage.py createsuperuser
```

---

## Production-розгортання

```bash
docker-compose -f docker-compose.prod.yml up -d
```

Production стек:
- Gunicorn (3 воркери, gthread, макс. 1000 запитів/воркер)
- Nginx як зворотний проксі з SSL-термінацією
- Certbot для автоматичного оновлення сертифікатів Let's Encrypt

Перевірка перед деплоєм:

```bash
python manage.py check --deploy
```

---

## Змінні середовища

| Змінна | Опис |
|--------|------|
| `SECRET_KEY` | Секретний ключ Django |
| `DEBUG` | `True` / `False` |
| `ALLOWED_HOSTS` | Список дозволених хостів через кому |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` | Облікові дані PostgreSQL |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` | Підключення до Redis |
| `HASHIDS_SALT` | Сіль для кодування реферальних кодів |
| `COUNTRY_STATE_CITY_API_KEY` | Ключ [CountryStateCity API](https://countrystatecity.in/) для геоданих |
| `GEO_API_KEY` | Ключ Google Maps API |
| `TIME_ZONE` | Часовий пояс Django (за замовчуванням: `UTC`) |
| `LANGUAGE_CODE` | Мова Django (за замовчуванням: `uk`) |

Повний шаблон — у файлі `.env.example`.

---

## Запуск тестів

```bash
# Усі тести
python manage.py test shop.tests --verbosity=2

# Один тест-клас
python manage.py test shop.tests.test_views.CreateProductViewTest

# З coverage-звітом
coverage run --source='shop' manage.py test shop.tests
coverage report

# Швидший запуск (паралельно + перевикористання БД)
python manage.py test shop.tests --parallel --keepdb
```

Тести розташовані у `shop/tests/` — `test_views.py`, `test_views_advanced.py`, `test_factories.py`.  
Покриття включає тести контролю доступу, валідації форм, геопошуку та ізоляції кешу через `DummyCache`.

---

## CI/CD Пайплайн

Пайплайн GitHub Actions запускається при push у гілки `main`/`develop` та на всі PR.

| Джоб | Що робить |
|------|----------|
| **Django** | Системна перевірка, валідація міграцій, тести з coverage |
| **Security (static)** | `pip-audit` (вразливості залежностей), `gitleaks` (пошук секретів), Semgrep SAST (правила Django), перевірка `--deploy` |
| **Security (dynamic)** | Запускає повний стек Nginx + Gunicorn; OWASP ZAP baseline scan + тест обмеження брутфорсу (очікується HTTP 429) |
| **Penetration testing** | Веб-сканер Nikto проти запущеного стеку |

---

## Ключові архітектурні рішення

### Пошук за радіусом (Гаверсинус)
Товари можна шукати у радіусі (км) від міста. Відстань розраховується на сервері за формулою Гаверсинуса на основі координат міста, збережених у таблиці `geo_city`.

### Реферальна система
`UserReferrals` зберігає реферальні зв'язки. Кожен код генерується через `hashids`-кодування первинного ключа — коди короткі та непередбачувані. Дерево обходиться рекурсивно — глибокі ланцюжки (100+ рівнів) загрожують `RecursionError`.

### Інвалідація кешу Redis
Django signals (`post_save`, `post_delete`) на моделях `Product` і `Categories` видаляють ключі кешу, підтримуючи актуальність списків без скидання по TTL.

### LoginRequiredMiddleware
Усі URL вимагають авторизації, окрім: `/`, `/users/login/`, `/users/signup/`, `/.well-known/`, `/health/`.

---

## Автор

Oleksii U.
https://github.com/evilsenpa1
