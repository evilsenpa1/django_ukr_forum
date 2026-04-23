"""
Fixtures and factories for shop application tests.

Constraints:
- Country.code is a unique field; pass different values when creating multiple countries.
- City.city_id is a unique CharField; set it explicitly when creating multiple cities.
- The Currency model was removed (migration 0005); Product.currency field does not exist.
"""

from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage

from geo.models import City, Country, Region
from shop.models import Categories, Product, ProductImage

User = get_user_model()


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user(username="testuser", email="test@test.com",
                    password="testpass123", **kwargs):
        return User.objects.create_user(
            username=username, email=email, password=password, **kwargs
        )

    @staticmethod
    def create_category(name="Електроніка", slug="electronics", **kwargs):
        return Categories.objects.create(name=name, slug=slug, **kwargs)

    @staticmethod
    def create_country(name="Україна", code="UA", **kwargs):
        return Country.objects.create(name=name, code=code, **kwargs)

    @staticmethod
    def create_region(name="Київська область", country=None, **kwargs):
        if country is None:
            country = TestDataFactory.create_country()
        return Region.objects.create(name=name, country=country, **kwargs)

    @staticmethod
    def create_city(name="Київ", region=None,
                    latitude=50.4501, longitude=30.5234,
                    city_id="kyiv-1", **kwargs):
        """City.country is set automatically from region in City.save()."""
        if region is None:
            region = TestDataFactory.create_region()
        return City.objects.create(
            name=name,
            region=region,
            latitude=latitude,
            longitude=longitude,
            city_id=city_id,
            **kwargs,
        )

    @staticmethod
    def create_product(name="Тестовий товар", author=None, category=None,
                       city=None, region=None, country=None,
                       price=1000, slug=None, **kwargs):
        if author is None:
            author = TestDataFactory.create_user()
        if category is None:
            category = TestDataFactory.create_category()
        if city is None:
            city = TestDataFactory.create_city()
        if region is None:
            region = city.region
        if country is None:
            country = city.country
        if slug is None:
            slug = name.lower().replace(" ", "-")

        return Product.objects.create(
            name=name,
            slug=slug,
            author=author,
            category=category,
            city=city,
            region=region,
            country=country,
            price=price,
            **kwargs,
        )

    @staticmethod
    def create_image(name="test.png", size=(200, 200), color="red"):
        """Returns a SimpleUploadedFile with a valid PNG image."""
        buf = BytesIO()
        PILImage.new("RGB", size, color=color).save(buf, "PNG")
        buf.seek(0)
        return SimpleUploadedFile(name=name, content=buf.read(),
                                  content_type="image/png")

    @staticmethod
    def create_product_image(product, image=None, **kwargs):
        if image is None:
            image = TestDataFactory.create_image()
        return ProductImage.objects.create(product=product, image=image, **kwargs)

    @staticmethod
    def create_complete_product_with_images(image_count=3, **product_kwargs):
        product = TestDataFactory.create_product(**product_kwargs)
        images = [
            TestDataFactory.create_product_image(
                product=product,
                image=TestDataFactory.create_image(name=f"image_{i}.png"),
            )
            for i in range(image_count)
        ]
        return product, images


class BaseTestWithData:
    """
    Creates a shared dataset once for the entire test class.
    Mix with django.test.TestCase: class MyTest(TestCase, BaseTestWithData): ...
    """

    @classmethod
    def setUpTestData(cls):
        cls.factory = TestDataFactory()

        cls.country = cls.factory.create_country(name="Україна", code="UA")
        cls.region = cls.factory.create_region(
            name="Київська область", country=cls.country
        )
        cls.city_kyiv = cls.factory.create_city(
            name="Київ", region=cls.region,
            latitude=50.4501, longitude=30.5234,
            city_id="kyiv-base",
        )
        cls.city_lviv = cls.factory.create_city(
            name="Львів", region=cls.region,
            latitude=49.8397, longitude=24.0297,
            city_id="lviv-base",
        )

        cls.user = cls.factory.create_user()
        cls.staff_user = cls.factory.create_user(
            username="staffuser", email="staff@test.com", is_staff=True
        )
        cls.other_user = cls.factory.create_user(
            username="otheruser", email="other@test.com"
        )

        cls.category_electronics = cls.factory.create_category(
            name="Електроніка", slug="electronics"
        )
        cls.category_clothes = cls.factory.create_category(
            name="Одяг", slug="clothes"
        )


class AuthenticatedTestMixin:
    """Automatically logs in self.user before each test."""

    def setUp(self):
        super().setUp()
        if hasattr(self, "user"):
            self.client.force_login(self.user)

    def login_as(self, user):
        self.client.force_login(user)

    def logout(self):
        self.client.logout()


class FileTestMixin:
    """Helper methods for working with files in tests."""

    def create_test_image(self, name="test.png", size=(200, 200), color="red"):
        return TestDataFactory.create_image(name, size, color)

    def create_multiple_images(self, count=3):
        colors = ["red", "blue", "green", "yellow", "purple", "orange"]
        return [
            self.create_test_image(name=f"image_{i}.png",
                                   color=colors[i % len(colors)])
            for i in range(count)
        ]
