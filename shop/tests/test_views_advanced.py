"""
Advanced tests for the shop application:
- Integration tests (full product lifecycle)
- Edge cases
- Access control
- Radius search (Haversine) — requires PostgreSQL + PostGIS functions
- File uploads
- Model validators
- Form validation

All bugs from the original file have been fixed (Currency removed, statuses,
URL kwargs, search filters, create form).
"""

import json
import shutil
import tempfile
from decimal import Decimal
from io import BytesIO

from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from geo.models import City, Country, Region
from shop.forms import ProductForm
from shop.models import (
    Categories, Product, ProductImage,
    validate_no_emoji, validate_image_size, validate_image_dimensions,
)

User = get_user_model()

DUMMY_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
# Disable SSL redirect so the test client (http://testserver) doesn't get 301s
TEST_OVERRIDES = {"CACHES": DUMMY_CACHE, "SECURE_SSL_REDIRECT": False}
TEMP_MEDIA = tempfile.mkdtemp()
TEMP_MEDIA_UPLOADS = tempfile.mkdtemp()  # separate dir for FileUploadTests


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def make_image(name="test.png", size=(200, 200), color="red"):
    buf = BytesIO()
    PILImage.new("RGB", size, color=color).save(buf, "PNG")
    buf.seek(0)
    return SimpleUploadedFile(name=name, content=buf.read(), content_type="image/png")


def base_setup(obj):
    """Common setUp for all classes — creates country, region, city, user, category."""
    obj.country = Country.objects.create(name="Україна", code="UA")
    obj.region = Region.objects.create(name="Київська обл.", country=obj.country)
    obj.city = City.objects.create(
        name="Київ", region=obj.region,
        latitude=50.4501, longitude=30.5234,
        city_id=f"kyiv-{obj.__class__.__name__}",
    )
    obj.category = Categories.objects.create(name="Електроніка", slug="electronics")
    obj.user = User.objects.create_user(
        username="testuser", email="test@test.com", password="testpass123"
    )


def valid_post_data(category_id, city_id, **overrides):
    data = {
        "name": "Тестовий товар",
        "description": "Опис тестового товару",
        "category": category_id,
        "price": "5000.00",
        "status": "new",
        "city_text": "Київ",
        "city_id": str(city_id),
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# IntegrationTests
# ---------------------------------------------------------------------------

@override_settings(**TEST_OVERRIDES, MEDIA_ROOT=TEMP_MEDIA)
class IntegrationTests(TestCase):
    """Full product lifecycle: create → view → update → delete."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        base_setup(self)

    def test_full_product_lifecycle(self):
        self.client.login(username="testuser", password="testpass123")

        # 1. Create
        response = self.client.post(
            reverse("shop:create_product"),
            valid_post_data(self.category.id, self.city.id, name="Інтеграційний тест"),
        )
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name="Інтеграційний тест")

        # 2. View
        detail_url = reverse("shop:product", kwargs={
            "category_slug": self.category.slug,
            "pk": product.pk,
            "product_slug": product.slug,
        })
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # 3. Update
        update_url = reverse("shop:update_product", kwargs={
            "pk": product.pk,
            "product_slug": product.slug,
        })
        response = self.client.post(
            update_url,
            valid_post_data(self.category.id, self.city.id,
                            name="Оновлений товар", price="4000.00"),
        )
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.name, "Оновлений товар")
        self.assertEqual(product.price, Decimal("4000.00"))

        # 4. Delete
        delete_url = reverse("shop:delete_product", kwargs={
            "pk": product.pk,
            "product_slug": product.slug,
        })
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_product_with_images_lifecycle(self):
        """Create a product with images, then delete one image."""
        self.client.login(username="testuser", password="testpass123")

        data = valid_post_data(self.category.id, self.city.id)
        data["images"] = [make_image("img1.png"), make_image("img2.png", color="blue")]
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 302)

        product = Product.objects.first()
        self.assertEqual(product.images.count(), 2)

        # Delete one image
        img = product.images.first()
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(product.images.count(), 1)

    def test_search_with_multiple_filters(self):
        category2 = Categories.objects.create(name="Одяг", slug="clothes")
        city2 = City.objects.create(
            name="Львів", region=self.region,
            latitude=49.8397, longitude=24.0297, city_id="lviv-integ",
        )

        Product.objects.create(
            name="iPhone в Києві", slug="iphone-kyiv",
            description="Смартфон", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country,
            price=25000, status="new",
        )
        Product.objects.create(
            name="Samsung у Львові", slug="samsung-lviv",
            description="Телефон", category=self.category,
            author=self.user, city=city2,
            region=self.region, country=self.country,
            price=20000, status="used",
        )
        Product.objects.create(
            name="Футболка в Києві", slug="futbolka-kyiv",
            description="Одяг", category=category2,
            author=self.user, city=self.city,
            region=self.region, country=self.country,
            price=500, status="new",
        )

        response = self.client.get(reverse("shop:search"), {
            "country_id": self.country.id,
            "region_id": self.region.id,
            "city_id": self.city.id,
            "status": "new",
            "category_id": self.category.id,
        })
        self.assertEqual(response.status_code, 200)
        products = list(response.context["Products"])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "iPhone в Києві")


# ---------------------------------------------------------------------------
# EdgeCaseTests
# ---------------------------------------------------------------------------

@override_settings(**TEST_OVERRIDES)
class EdgeCaseTests(TestCase):
    """Boundary conditions and edge cases."""

    def setUp(self):
        self.client = Client()
        base_setup(self)

    def test_search_with_invalid_page_number(self):
        """Non-numeric page value — Paginator falls back to page 1."""
        response = self.client.get(reverse("shop:search"), {"page": "invalid"})
        self.assertEqual(response.status_code, 200)

    def test_search_with_page_beyond_last(self):
        """Page number exceeding the maximum — Paginator returns the last page."""
        response = self.client.get(reverse("shop:search"), {"page": 9999})
        self.assertEqual(response.status_code, 200)

    def test_search_empty_query_returns_all(self):
        Product.objects.create(
            name="Товар", slug="tovar",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        response = self.client.get(reverse("shop:search"), {"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 1)

    def test_create_product_name_at_max_length(self):
        """150 characters — valid."""
        self.client.login(username="testuser", password="testpass123")
        data = valid_post_data(
            self.category.id, self.city.id, name="А" * 150,
        )
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.count(), 1)

    def test_create_product_name_over_max_length(self):
        """151 characters — form error."""
        self.client.login(username="testuser", password="testpass123")
        data = valid_post_data(self.category.id, self.city.id, name="А" * 151)
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_emoji_in_name_rejected(self):
        """Emoji in the product name are not allowed."""
        self.client.login(username="testuser", password="testpass123")
        data = valid_post_data(self.category.id, self.city.id, name="Товар 😀")
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), 0)

    def test_delete_image_twice_returns_404(self):
        """Second delete request for an already-deleted image returns 404."""
        self.client.login(username="testuser", password="testpass123")
        product = Product.objects.create(
            name="Тест", slug="test-del2",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        img = ProductImage.objects.create(product=product, image=make_image())

        url = reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        response1 = self.client.post(url)
        self.assertEqual(response1.status_code, 200)

        # 404 template uses {% url 'articles:...' %} — disable exception propagation
        self.client.raise_request_exception = False
        response2 = self.client.post(url)
        self.client.raise_request_exception = True
        self.assertEqual(response2.status_code, 404)

    def test_update_product_invalid_category(self):
        """Non-existent category — form is invalid."""
        self.client.login(username="testuser", password="testpass123")
        product = Product.objects.create(
            name="Тест", slug="test-inv-cat",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        data = valid_post_data(99999, self.city.id, name="Оновлений товар")
        response = self.client.post(
            reverse("shop:update_product", kwargs={
                "pk": product.pk, "product_slug": product.slug,
            }),
            data,
        )
        self.assertEqual(response.status_code, 200)  # UpdateView does not override form_invalid
        self.assertIn("category", response.context["form"].errors)

    def test_search_nonexistent_category_id(self):
        """Non-existent category_id — returns all products (category not found)."""
        response = self.client.get(reverse("shop:search"), {"category_id": 99999})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Усі товари", response.context["title"])

    def test_my_products_empty_for_new_user(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("shop:my_products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["products"]), 0)


# ---------------------------------------------------------------------------
# PermissionTests
# ---------------------------------------------------------------------------

@override_settings(**TEST_OVERRIDES, MEDIA_ROOT="/tmp/test_media_perm/")
class PermissionTests(TestCase):
    """Access control tests."""

    def setUp(self):
        self.client = Client()
        base_setup(self)
        self.staff_user = User.objects.create_user(
            username="staff", email="staff@test.com",
            password="testpass123", is_staff=True,
        )
        self.product = Product.objects.create(
            name="iPhone 14", slug="iphone-perm",
            description="Смартфон", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=25000,
        )

    def test_staff_can_delete_image_of_other_user(self):
        self.client.login(username="staff", password="testpass123")
        img = ProductImage.objects.create(product=self.product, image=make_image())
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProductImage.objects.filter(id=img.id).exists())

    def test_staff_can_update_product_of_other_user(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("shop:update_product", kwargs={
            "pk": self.product.pk, "product_slug": self.product.slug,
        }))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_delete_product_of_other_user(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("shop:delete_product", kwargs={
            "pk": self.product.pk, "product_slug": self.product.slug,
        }))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_anonymous_cannot_create_product(self):
        response = self.client.post(
            reverse("shop:create_product"),
            valid_post_data(self.category.id, self.city.id),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertEqual(Product.objects.count(), 1)  # only self.product

    def test_anonymous_cannot_update_product(self):
        response = self.client.post(reverse("shop:update_product", kwargs={
            "pk": self.product.pk, "product_slug": self.product.slug,
        }), valid_post_data(self.category.id, self.city.id))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_anonymous_cannot_delete_product(self):
        response = self.client.post(reverse("shop:delete_product", kwargs={
            "pk": self.product.pk, "product_slug": self.product.slug,
        }))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

    def test_other_user_cannot_update_product(self):
        other = User.objects.create_user(
            username="other2", email="other2@t.com", password="testpass123"
        )
        self.client.force_login(other)
        response = self.client.post(reverse("shop:update_product", kwargs={
            "pk": self.product.pk, "product_slug": self.product.slug,
        }), valid_post_data(self.category.id, self.city.id))
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# HaversineSearchTest — requires PostgreSQL with math function support
# ---------------------------------------------------------------------------

@override_settings(**TEST_OVERRIDES)
class HaversineSearchTest(TestCase):
    """
    Radius search tests (Haversine formula).
    Requires PostgreSQL + pg_trgm extension.
    city_id filter only applies when country_id + region_id + city_id are all provided.
    """

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)

        # Kyiv — reference point
        self.city_kyiv = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-haversine",
        )
        # Brovary — ~20 km from Kyiv
        self.city_brovary = City.objects.create(
            name="Бровари", region=self.region,
            latitude=50.5108, longitude=30.7939, city_id="brovary-haversine",
        )
        # Bila Tserkva — ~85 km from Kyiv
        self.city_bila_tserkva = City.objects.create(
            name="Біла Церква", region=self.region,
            latitude=49.7978, longitude=30.1119, city_id="bila-tserkva-haversine",
        )

        self.category = Categories.objects.create(
            name="Електроніка", slug="electronics-hav"
        )
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )

        Product.objects.create(
            name="Товар у Києві", slug="tovar-kyiv",
            description="Опис", category=self.category, author=self.user,
            city=self.city_kyiv, region=self.region, country=self.country, price=1000,
        )
        Product.objects.create(
            name="Товар у Броварах", slug="tovar-brovary",
            description="Опис", category=self.category, author=self.user,
            city=self.city_brovary, region=self.region, country=self.country, price=2000,
        )
        Product.objects.create(
            name="Товар у Білій Церкві", slug="tovar-bila",
            description="Опис", category=self.category, author=self.user,
            city=self.city_bila_tserkva, region=self.region, country=self.country, price=3000,
        )

    def _search(self, radius):
        return self.client.get(reverse("shop:search"), {
            "country_id": self.country.id,
            "region_id": self.region.id,
            "city_id": self.city_kyiv.id,
            "radius": radius,
        })

    def test_radius_10km_returns_only_kyiv(self):
        response = self._search(10)
        self.assertEqual(response.status_code, 200)
        products = list(response.context["Products"])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].city, self.city_kyiv)

    def test_radius_30km_returns_kyiv_and_brovary(self):
        response = self._search(30)
        self.assertEqual(response.status_code, 200)
        products = list(response.context["Products"])
        self.assertEqual(len(products), 2)
        cities = {p.city for p in products}
        self.assertIn(self.city_kyiv, cities)
        self.assertIn(self.city_brovary, cities)

    def test_radius_100km_returns_all(self):
        response = self._search(100)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 3)

    def test_radius_without_city_is_ignored(self):
        """radius without city_id is ignored — all products are returned."""
        response = self.client.get(reverse("shop:search"), {"radius": 30})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 3)


# ---------------------------------------------------------------------------
# FileUploadTests
# ---------------------------------------------------------------------------

@override_settings(**TEST_OVERRIDES, MEDIA_ROOT=TEMP_MEDIA_UPLOADS)
class FileUploadTests(TestCase):
    """Image upload tests."""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_UPLOADS, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        base_setup(self)

    def test_create_product_with_multiple_images(self):
        self.client.login(username="testuser", password="testpass123")
        data = valid_post_data(self.category.id, self.city.id, name="Товар з фото")
        data["images"] = [
            make_image("img1.png", color="red"),
            make_image("img2.png", color="blue"),
            make_image("img3.png", color="green"),
        ]
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 302)
        product = Product.objects.first()
        self.assertEqual(product.images.count(), 3)

    def test_update_product_adds_images(self):
        self.client.login(username="testuser", password="testpass123")
        product = Product.objects.create(
            name="Тест", slug="test-upd-img",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        data = valid_post_data(self.category.id, self.city.id, name="Оновлений")
        data["images"] = [make_image()]
        response = self.client.post(
            reverse("shop:update_product", kwargs={
                "pk": product.pk, "product_slug": product.slug,
            }),
            data,
        )
        self.assertEqual(response.status_code, 302)
        product.refresh_from_db()
        self.assertEqual(product.images.count(), 1)

    def test_update_product_delete_images_via_json(self):
        """Delete images via the deleted_images field (JSON list of ids)."""
        self.client.login(username="testuser", password="testpass123")
        product = Product.objects.create(
            name="Тест", slug="test-del-img",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        img = ProductImage.objects.create(product=product, image=make_image())

        data = valid_post_data(self.category.id, self.city.id, name="Оновлений")
        data["deleted_images"] = json.dumps([img.id])
        response = self.client.post(
            reverse("shop:update_product", kwargs={
                "pk": product.pk, "product_slug": product.slug,
            }),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProductImage.objects.filter(id=img.id).exists())

    def test_image_ordering_increments(self):
        """Image ordering value increments automatically."""
        product = Product.objects.create(
            name="Тест", slug="test-ordering",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        img1 = ProductImage.objects.create(product=product, image=make_image("a.png"))
        img2 = ProductImage.objects.create(product=product, image=make_image("b.png"))
        self.assertGreater(img2.ordering, img1.ordering)


# ---------------------------------------------------------------------------
# ModelValidationTests
# ---------------------------------------------------------------------------

class ModelValidationTests(TestCase):
    """Model validator tests (no HTTP requests)."""

    def setUp(self):
        base_setup(self)

    # --- validate_no_emoji ---

    def test_validate_no_emoji_passes_for_normal_text(self):
        """Normal text does not raise an exception."""
        validate_no_emoji("Нормальна назва товару 123")

    def test_validate_no_emoji_raises_for_emoji(self):
        with self.assertRaises(ValidationError):
            validate_no_emoji("Товар 😀")

    def test_validate_no_emoji_raises_for_various_emoji(self):
        for name in ["🚀 Ракета", "📱 Телефон", "Товар ❤️"]:
            with self.assertRaises(ValidationError):
                validate_no_emoji(name)

    # --- validate_image_size ---

    def test_validate_image_size_passes_valid_image(self):
        # Solid-color PNGs compress aggressively; use 500x500 to guarantee > 1024 bytes
        img = make_image(size=(500, 500))
        validate_image_size(img)

    def test_validate_image_size_too_small(self):
        tiny = SimpleUploadedFile("tiny.png", b"x" * 100, content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_image_size(tiny)

    # --- validate_image_dimensions ---

    def test_validate_image_dimensions_passes_valid(self):
        img = make_image(size=(200, 200))
        validate_image_dimensions(img)

    def test_validate_image_dimensions_too_small(self):
        img = make_image(size=(50, 50))
        with self.assertRaises(ValidationError):
            validate_image_dimensions(img)

    def test_validate_image_dimensions_bad_aspect_ratio(self):
        """Aspect ratio > 20 is not allowed."""
        img = make_image(size=(2100, 100))
        with self.assertRaises(ValidationError):
            validate_image_dimensions(img)

    # --- ProductImage.clean() — 10 image limit ---

    def test_product_image_limit_10(self):
        """Cannot add more than 10 images to a single product."""
        product = Product.objects.create(
            name="Тест", slug="test-img-limit",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        for i in range(10):
            ProductImage.objects.create(product=product, image=make_image(f"img{i}.png"))

        eleventh = ProductImage(product=product, image=make_image("img11.png"))
        with self.assertRaises(ValidationError):
            eleventh.clean()

    # --- Product.date_update is set on save ---

    def test_product_date_update_set_on_save(self):
        product = Product.objects.create(
            name="Тест", slug="test-dateupd",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        self.assertIsNone(product.date_update)  # not set on initial creation

        product.price = 2000
        product.save()
        product.refresh_from_db()
        self.assertIsNotNone(product.date_update)

    # --- Product.slug uniqueness ---

    def test_product_slug_must_be_unique(self):
        from django.db import IntegrityError
        Product.objects.create(
            name="Товар 1", slug="duplicate-slug",
            description="Опис", category=self.category,
            author=self.user, city=self.city,
            region=self.region, country=self.country, price=1000,
        )
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name="Товар 2", slug="duplicate-slug",
                description="Опис", category=self.category,
                author=self.user, city=self.city,
                region=self.region, country=self.country, price=2000,
            )


# ---------------------------------------------------------------------------
# FormValidationTests
# ---------------------------------------------------------------------------

class FormValidationTests(TestCase):
    """ProductForm tests (no HTTP requests)."""

    def setUp(self):
        base_setup(self)

    def _form_data(self, **overrides):
        data = {
            "name": "Тестовий товар",
            "description": "Опис товару достатньої довжини",
            "category": self.category.id,
            "price": "1000.00",
            "status": "new",
            "city_text": "Київ",
            "city_id": str(self.city.id),
        }
        data.update(overrides)
        return data

    def test_form_valid_with_correct_data(self):
        form = ProductForm(data=self._form_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_without_city_id(self):
        data = self._form_data()
        del data["city_id"]
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())

    def test_form_invalid_price_zero(self):
        form = ProductForm(data=self._form_data(price="0"))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_form_invalid_price_negative(self):
        form = ProductForm(data=self._form_data(price="-10"))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_form_invalid_price_too_high(self):
        form = ProductForm(data=self._form_data(price="100000.00"))
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_form_valid_price_boundary_max(self):
        form = ProductForm(data=self._form_data(price="99999.99"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_price_boundary_min(self):
        form = ProductForm(data=self._form_data(price="0.01"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_empty_name(self):
        form = ProductForm(data=self._form_data(name=""))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_form_invalid_name_too_long(self):
        form = ProductForm(data=self._form_data(name="А" * 151))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_form_save_sets_city_region_country(self):
        """form.save() correctly assigns city, region, and country."""
        form = ProductForm(data=self._form_data())
        self.assertTrue(form.is_valid(), form.errors)
        product = form.save(commit=False)
        self.assertEqual(product.city, self.city)
        self.assertEqual(product.region, self.region)
        self.assertEqual(product.country, self.country)

    def test_form_invalid_nonexistent_category(self):
        form = ProductForm(data=self._form_data(category=99999))
        self.assertFalse(form.is_valid())
        self.assertIn("category", form.errors)
