# Тесты приложения shop

## Файлы

### test_factories.py
Фикстуры и вспомогательные классы:

| Класс / функция | Назначение |
|-----------------|-----------|
| `TestDataFactory` | Статические методы для создания тестовых объектов (user, category, city, product, image) |
| `BaseTestWithData` | Миксин с `setUpTestData` — общий набор объектов на весь тестовый класс |
| `AuthenticatedTestMixin` | Автологин `self.user` в `setUp`, методы `login_as` / `logout` |
| `FileTestMixin` | Хелперы для создания тестовых PNG-изображений |

**Ограничения при создании объектов:**
- `Country.code` — уникальное поле, передавайте разные значения для разных стран
- `City.city_id` — уникальное поле, явно задавайте при создании нескольких городов

---

### test_views.py
Основные HTTP-тесты представлений:

| Класс | Что проверяет |
|-------|--------------|
| `CatalogViewTest` | Рендер главной страницы, список категорий и товаров, анонимный доступ |
| `SearchViewTest` | Фильтрация по категории, региону, городу, статусу; сортировка; пагинация |
| `RedirectToCategoryViewTest` | Редирект с `category_id`, без него и для несуществующего id |
| `ReadProductViewTest` | Требование авторизации, рендер детальной страницы, 404 |
| `CreateProductViewTest` | Авторизация, валидация формы, загрузка изображений, автозаполнение региона/страны |
| `UpdateProductViewTest` | Права владельца, успешное обновление, доступ staff |
| `DeleteProductImageViewTest` | POST-only, права владельца, JSON-ответ, 404 для несуществующего |
| `DeleteProductViewTest` | Права владельца, страница подтверждения, доступ staff |
| `MyProductsViewTest` | Изоляция товаров по автору, пагинация |

---

### test_views_advanced.py
Расширенные тесты:

| Класс | Что проверяет |
|-------|--------------|
| `IntegrationTests` | Полный цикл товара: создание → просмотр → редактирование → удаление |
| `EdgeCaseTests` | Граничные случаи: эмодзи в названии, длина поля, повторное удаление, невалидная пагинация |
| `PermissionTests` | Staff vs. owner vs. аноним для create / update / delete |
| `HaversineSearchTest` | Геопоиск по радиусу (10 / 30 / 100 км) — **требует PostgreSQL** |
| `FileUploadTests` | Загрузка нескольких изображений, удаление через `deleted_images`, ordering |
| `ModelValidationTests` | Валидаторы `validate_no_emoji`, `validate_image_size`, `validate_image_dimensions`, лимит 10 фото, уникальность slug |
| `FormValidationTests` | `ProductForm`: граничные значения цены, обязательные поля, проставление city/region/country |

---

## Запуск

```bash
# Все тесты
python manage.py test shop.tests --verbosity=2

# Один класс
python manage.py test shop.tests.test_views.CreateProductViewTest

# С покрытием
coverage run --source='shop' manage.py test shop.tests
coverage report

# Ускорение (параллельно + переиспользовать БД)
python manage.py test shop.tests --parallel --keepdb
```

## Особенности

- Все HTTP-тесты используют `@override_settings(CACHES=DUMMY_CACHE)` — кеш отключён.
- `HaversineSearchTest` требует PostgreSQL; на SQLite-окружении пропускается/падает.
- Тесты с файлами переопределяют `MEDIA_ROOT` через `@override_settings`.
- `CreateProduct.form_invalid` возвращает **HTTP 400** (переопределено во view).
- `UpdateView.form_invalid` возвращает **HTTP 200** (стандартное поведение Django).
