"""
View tests for the shop application.

Documented behavioral characteristics:
- status: 'new' / 'used' (not 'active' / 'sold')
- update/delete URLs require pk + product_slug
- redirect_to_category accepts category_id (int)
- Filtering by city/region in search requires country_id
- CreateProduct.form_invalid returns 400
- Cache disabled via DummyCache
"""

from io import BytesIO

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from geo.models import City, Country, Region
from shop.models import Categories, Product, ProductImage

User = get_user_model()

DUMMY_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
# Disable SSL redirect so the test client (http://testserver) doesn't get 301s
TEST_OVERRIDES = {"CACHES": DUMMY_CACHE, "SECURE_SSL_REDIRECT": False}


def make_image(name="test.png", size=(200, 200), color="red"):
    buf = BytesIO()
    PILImage.new("RGB", size, color=color).save(buf, "PNG")
    buf.seek(0)
    return SimpleUploadedFile(name=name, content=buf.read(), content_type="image/png")


@override_settings(**TEST_OVERRIDES)
class CatalogViewTest(TestCase):
    """Tests for the catalog index page (shop:index)."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-catalog",
        )
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")

    def test_catalog_view_renders_correctly(self):
        response = self.client.get(reverse("shop:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/index.html")
        self.assertIn("Category", response.context)
        self.assertIn("Products", response.context)
        self.assertIn("RADII", response.context)
        self.assertEqual(response.context["title"], "Торгівля")

    def test_catalog_shows_all_categories(self):
        """Category in context is a list, not a queryset."""
        Categories.objects.create(name="Одяг", slug="clothes")
        Categories.objects.create(name="Меблі", slug="furniture")
        response = self.client.get(reverse("shop:index"))
        self.assertEqual(len(response.context["Category"]), 3)

    def test_catalog_returns_latest_products(self):
        Product.objects.create(
            name="Ноутбук", slug="noutbuk",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=15000,
        )
        response = self.client.get(reverse("shop:index"))
        names = [p["name"] for p in response.context["Products"]]
        self.assertIn("Ноутбук", names)

    def test_catalog_accessible_without_login(self):
        """Catalog index page is accessible anonymously."""
        response = self.client.get(reverse("shop:index"))
        self.assertEqual(response.status_code, 200)


@override_settings(**TEST_OVERRIDES)
class SearchViewTest(TestCase):
    """Tests for the search view."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-search",
        )
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")

        self.product1 = Product.objects.create(
            name="iPhone 14", slug="iphone-14",
            description="Новий смартфон",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=25000, status="new",
        )
        self.product2 = Product.objects.create(
            name="Samsung Galaxy", slug="samsung-galaxy",
            description="Хороший телефон",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=20000, status="used",
        )

    def test_search_without_query(self):
        response = self.client.get(reverse("shop:search"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/product_list.html")
        self.assertEqual(response.context["Products"].paginator.count, 2)

    def test_search_by_category(self):
        category2 = Categories.objects.create(name="Одяг", slug="clothes")
        Product.objects.create(
            name="Футболка", slug="futbolka",
            description="Одяг",
            category=category2, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=500,
        )
        response = self.client.get(
            reverse("shop:search"), {"category_id": self.category.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 2)
        self.assertIn(self.category.name, response.context["title"])

    def test_search_by_region_requires_country(self):
        """region_id without country_id is ignored — all products are returned."""
        response = self.client.get(
            reverse("shop:search"), {"region_id": self.region.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 2)

    def test_search_by_region_with_country(self):
        """region_id + country_id filters by region."""
        response = self.client.get(reverse("shop:search"), {
            "country_id": self.country.id,
            "region_id": self.region.id,
        })
        self.assertEqual(response.status_code, 200)
        products = list(response.context["Products"])
        self.assertTrue(all(p.region == self.region for p in products))

    def test_search_by_city_with_country_and_region(self):
        """city_id filters only when country_id + region_id are present."""
        response = self.client.get(reverse("shop:search"), {
            "country_id": self.country.id,
            "region_id": self.region.id,
            "city_id": self.city.id,
        })
        self.assertEqual(response.status_code, 200)
        products = list(response.context["Products"])
        self.assertTrue(all(p.city == self.city for p in products))

    def test_search_by_status_new(self):
        response = self.client.get(reverse("shop:search"), {"status": "new"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 1)
        self.assertEqual(list(response.context["Products"])[0].name, "iPhone 14")

    def test_search_by_status_used(self):
        response = self.client.get(reverse("shop:search"), {"status": "used"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 1)

    def test_search_invalid_status_ignored(self):
        """Unknown status value is ignored — all products are returned."""
        response = self.client.get(reverse("shop:search"), {"status": "active"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["Products"].paginator.count, 2)

    def test_search_pagination(self):
        for i in range(15):
            Product.objects.create(
                name=f"Product {i}", slug=f"product-{i}",
                description="Test",
                category=self.category, author=self.user,
                city=self.city, region=self.region, country=self.country,
                price=1000,
            )
        # Total 17 products, page 2 = 7
        response = self.client.get(reverse("shop:search"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["Products"]), 7)

    def test_search_context_has_required_keys(self):
        response = self.client.get(reverse("shop:search"))
        for key in ("title", "Products", "Category", "q", "RADII"):
            self.assertIn(key, response.context)

    def test_search_date_sort_asc(self):
        response = self.client.get(reverse("shop:search"), {"date_sort": "date"})
        self.assertEqual(response.status_code, 200)

    def test_search_date_sort_desc(self):
        response = self.client.get(reverse("shop:search"), {"date_sort": "-date"})
        self.assertEqual(response.status_code, 200)


@override_settings(**TEST_OVERRIDES)
class RedirectToCategoryViewTest(TestCase):
    """Tests for the redirect_to_category view."""

    def setUp(self):
        self.client = Client()
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")

    def test_redirect_with_category_id(self):
        response = self.client.get(
            reverse("shop:redirect_to_category"),
            {"category_id": self.category.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(str(self.category.id), response.url)

    def test_redirect_without_category_id_goes_to_index(self):
        """Without category_id — redirects to shop:index."""
        response = self.client.get(reverse("shop:redirect_to_category"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shop:index"))

    def test_redirect_with_nonexistent_category_returns_404(self):
        # 404 template uses {% url 'articles:...' %} — disable exception propagation
        self.client.raise_request_exception = False
        response = self.client.get(
            reverse("shop:redirect_to_category"), {"category_id": 99999}
        )
        self.client.raise_request_exception = True
        self.assertEqual(response.status_code, 404)

    def test_redirect_with_invalid_category_id_goes_to_index(self):
        """Non-numeric category_id — redirects to shop:index."""
        response = self.client.get(
            reverse("shop:redirect_to_category"), {"category_id": "abc"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shop:index"))


@override_settings(**TEST_OVERRIDES)
class ReadProductViewTest(TestCase):
    """Tests for the ReadProduct view (shop:product)."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-read",
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="iPhone 14", slug="iphone-14",
            description="Смартфон",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=25000,
        )

    def _url(self):
        return reverse("shop:product", kwargs={
            "category_slug": self.category.slug,
            "pk": self.product.pk,
            "product_slug": self.product.slug,
        })

    def test_read_product_requires_login(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_read_product_renders_correctly(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/product_cart.html")

    def test_read_product_context_has_object(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self._url())
        self.assertEqual(response.context["object"], self.product)

    def test_read_nonexistent_product_returns_404(self):
        self.client.login(username="testuser", password="testpass123")
        url = reverse("shop:product", kwargs={
            "category_slug": self.category.slug,
            "pk": 99999,
            "product_slug": "nonexistent-slug",
        })
        # 404 template uses {% url 'articles:...' %} — disable exception propagation
        self.client.raise_request_exception = False
        response = self.client.get(url)
        self.client.raise_request_exception = True
        self.assertEqual(response.status_code, 404)


@override_settings(**TEST_OVERRIDES, MEDIA_ROOT="/tmp/test_media_create/")
class CreateProductViewTest(TestCase):
    """Tests for the CreateProduct view."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-create",
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )

    def _valid_data(self, **overrides):
        data = {
            "name": "Новий товар",
            "description": "Опис товару для тесту",
            "category": self.category.id,
            "price": "1000.00",
            "status": "new",
            "city_text": "Київ",
            "city_id": str(self.city.id),
        }
        data.update(overrides)
        return data

    def test_create_product_requires_login(self):
        response = self.client.get(reverse("shop:create_product"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_create_product_get(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("shop:create_product"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/create_product.html")
        self.assertEqual(response.context["title"], "Додання товару")
        self.assertIn("categories", response.context)

    def test_create_product_successful(self):
        """Verifies auto-population of author, region, country from city."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("shop:create_product"), self._valid_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.count(), 1)

        product = Product.objects.first()
        self.assertEqual(product.name, "Новий товар")
        self.assertEqual(product.author, self.user)
        self.assertEqual(product.city, self.city)
        self.assertEqual(product.region, self.region)
        self.assertEqual(product.country, self.country)
        self.assertIsNotNone(product.slug)

    def test_create_product_with_images(self):
        self.client.login(username="testuser", password="testpass123")
        data = self._valid_data()
        data["images"] = [make_image("img1.png", color="red"), make_image("img2.png", color="blue")]
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.first().images.count(), 2)

    def test_create_product_invalid_missing_city(self):
        """Without city_id the form is invalid — view returns 400."""
        self.client.login(username="testuser", password="testpass123")
        data = self._valid_data()
        del data["city_id"]
        response = self.client.post(reverse("shop:create_product"), data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_invalid_price_zero(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("shop:create_product"), self._valid_data(price="0"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_invalid_price_too_high(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("shop:create_product"), self._valid_data(price="100000.00"))
        self.assertEqual(response.status_code, 400)

    def test_create_product_invalid_name_too_long(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(reverse("shop:create_product"), self._valid_data(name="А" * 151))
        self.assertEqual(response.status_code, 400)

    def test_anonymous_cannot_create_product(self):
        response = self.client.post(reverse("shop:create_product"), self._valid_data())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertEqual(Product.objects.count(), 0)


@override_settings(**TEST_OVERRIDES)
class UpdateProductViewTest(TestCase):
    """Tests for the UpdateProduct view."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-update",
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@test.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="iPhone 14", slug="iphone-14",
            description="Новий смартфон",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=25000,
        )

    def _url(self):
        return reverse("shop:update_product", kwargs={
            "pk": self.product.pk,
            "product_slug": self.product.slug,
        })

    def _valid_data(self, **overrides):
        data = {
            "name": "Оновлений iPhone",
            "description": "Нова ціна",
            "category": self.category.id,
            "price": "20000.00",
            "status": "used",
            "city_text": "Київ",
            "city_id": str(self.city.id),
        }
        data.update(overrides)
        return data

    def test_update_requires_login(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_update_requires_owner(self):
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_update_get(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/update_product.html")
        self.assertEqual(response.context["title"], "Редагування товару")

    def test_update_successful(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self._url(), self._valid_data())
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Оновлений iPhone")
        from decimal import Decimal
        self.assertEqual(self.product.price, Decimal("20000.00"))

    def test_staff_can_update_any_product(self):
        staff = User.objects.create_user(
            username="staff", email="staff@test.com",
            password="testpass123", is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)

    def test_update_sets_date_update(self):
        self.client.login(username="testuser", password="testpass123")
        self.client.post(self._url(), self._valid_data())
        self.product.refresh_from_db()
        self.assertIsNotNone(self.product.date_update)


@override_settings(**TEST_OVERRIDES, MEDIA_ROOT="/tmp/test_media_delimg/")
class DeleteProductImageViewTest(TestCase):
    """Tests for the delete_product_image view."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-delimg",
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@test.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="iPhone 14", slug="iphone-14",
            description="Смартфон",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=25000,
        )

    def _make_product_image(self):
        return ProductImage.objects.create(product=self.product, image=make_image())

    def test_delete_image_requires_login(self):
        img = self._make_product_image()
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_image_requires_post(self):
        """GET requests are not allowed — returns 405."""
        self.client.login(username="testuser", password="testpass123")
        img = self._make_product_image()
        response = self.client.get(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_delete_image_by_owner(self):
        self.client.login(username="testuser", password="testpass123")
        img = self._make_product_image()
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})
        self.assertFalse(ProductImage.objects.filter(id=img.id).exists())

    def test_delete_image_by_non_owner_forbidden(self):
        self.client.login(username="otheruser", password="testpass123")
        img = self._make_product_image()
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ProductImage.objects.filter(id=img.id).exists())

    def test_delete_nonexistent_image_returns_404(self):
        self.client.login(username="testuser", password="testpass123")
        # 404 template uses {% url 'articles:...' %} — disable exception propagation
        self.client.raise_request_exception = False
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": 99999})
        )
        self.client.raise_request_exception = True
        self.assertEqual(response.status_code, 404)

    def test_delete_image_response_is_json(self):
        self.client.login(username="testuser", password="testpass123")
        img = self._make_product_image()
        response = self.client.post(
            reverse("shop:delete_product_image", kwargs={"image_id": img.id})
        )
        self.assertEqual(response["Content-Type"], "application/json")


@override_settings(**TEST_OVERRIDES)
class DeleteProductViewTest(TestCase):
    """Tests for the DeleteProduct view."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-del",
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@test.com", password="testpass123"
        )
        self.product = Product.objects.create(
            name="iPhone 14", slug="iphone-14",
            description="Смартфон",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=25000,
        )

    def _url(self):
        return reverse("shop:delete_product", kwargs={
            "pk": self.product.pk,
            "product_slug": self.product.slug,
        })

    def test_delete_requires_login(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_delete_requires_owner(self):
        self.client.login(username="otheruser", password="testpass123")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 403)

    def test_delete_get_shows_confirmation(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/delete_product.html")

    def test_delete_successful(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("shop:index"))
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_staff_can_delete_any_product(self):
        staff = User.objects.create_user(
            username="staff", email="staff@t.com",
            password="testpass123", is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.post(self._url())
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())


@override_settings(**TEST_OVERRIDES)
class MyProductsViewTest(TestCase):
    """Tests for the MyProducts view."""

    def setUp(self):
        self.client = Client()
        self.country = Country.objects.create(name="Україна", code="UA")
        self.region = Region.objects.create(name="Київська обл.", country=self.country)
        self.city = City.objects.create(
            name="Київ", region=self.region,
            latitude=50.4501, longitude=30.5234, city_id="kyiv-my",
        )
        self.category = Categories.objects.create(name="Електроніка", slug="electronics")
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass123"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@test.com", password="testpass123"
        )

    def test_my_products_requires_login(self):
        response = self.client.get(reverse("shop:my_products"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_my_products_empty(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("shop:my_products"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["products"]), 0)

    def test_my_products_shows_only_own(self):
        """Other users' products are not included in the list."""
        self.client.login(username="testuser", password="testpass123")
        Product.objects.create(
            name="Мій товар", slug="miy-tovar",
            category=self.category, author=self.user,
            city=self.city, region=self.region, country=self.country,
            price=1000,
        )
        Product.objects.create(
            name="Чужий товар", slug="chuzhyi-tovar",
            category=self.category, author=self.other_user,
            city=self.city, region=self.region, country=self.country,
            price=2000,
        )
        response = self.client.get(reverse("shop:my_products"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "shop_temp/my_products.html")
        self.assertEqual(response.context["title"], "Мої товари")
        self.assertEqual(len(response.context["products"]), 1)
        self.assertEqual(response.context["products"][0].name, "Мій товар")

    def test_my_products_pagination(self):
        self.client.login(username="testuser", password="testpass123")
        for i in range(15):
            Product.objects.create(
                name=f"Товар {i}", slug=f"product-{i}",
                category=self.category, author=self.user,
                city=self.city, region=self.region, country=self.country,
                price=1000,
            )
        response = self.client.get(reverse("shop:my_products"))
        self.assertEqual(len(response.context["products"]), 10)

        response2 = self.client.get(reverse("shop:my_products"), {"page": 2})
        self.assertEqual(len(response2.context["products"]), 5)

    def test_my_products_context_keys(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("shop:my_products"))
        self.assertIn("products", response.context)
        self.assertIn("title", response.context)
