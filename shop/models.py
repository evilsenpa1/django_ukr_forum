from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

import re
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from PIL import Image

from geo.models import Country, Region, City


class Categories(models.Model):

    name = models.CharField(
        max_length=50,
        verbose_name="Назва категорії",
        blank=False,
        null=False,
        unique=True,
    )
    img = models.ImageField(
        upload_to="category_images", verbose_name="Зображення", blank=True, null=True
    )

    slug = models.SlugField(max_length=200, verbose_name="URL", unique=True)

    class Meta:
        db_table = "categories"
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name





def validate_no_emoji(value):
    """Reject emoji and non-BMP Unicode characters in product names."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )

    if emoji_pattern.search(value):
        raise ValidationError(
            _('Emoji are not allowed in the product name'),
            code='no_emoji'
        )



class Product(models.Model):

    name = models.CharField(
        max_length=150, verbose_name="Назва товару", blank=False, null=False, validators=[validate_no_emoji]
    )
    description = models.TextField(verbose_name="Опис", max_length=1500)
    slug = models.SlugField(max_length=200, verbose_name="URL", unique=True)
    price = models.DecimalField(
        blank=False,
        null=False,
        default=0,
        max_digits=10,
        decimal_places=2,
        verbose_name="Ціна",
    )
    date = models.DateField(auto_now_add=True, verbose_name="Дата", db_index=True)

    date_update = models.DateTimeField(null=True, blank=True, verbose_name="Дата редагування")

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )


    category = models.ForeignKey(
        "Categories", verbose_name="Категорія", on_delete=models.CASCADE
    )

    STATUS_CHOICES = [
        ('new', 'Новий'),
        ('used', 'Б/В'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
    )

    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )

    region = models.ForeignKey(
        Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )

    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )

    class Meta:
        db_table = "products"
        verbose_name = "Товар"
        verbose_name_plural = "Товари"



    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.pk:
            self.date_update = timezone.now()
        super().save(*args, **kwargs)
    





def validate_image_size(image):
    """Check file size: must be between 1 KB and 10 MB."""
    if not image:
        return
    max_size_mb = 10
    if image.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f'Максимальний розмір файлу: {max_size_mb}MB')
    if image.size < 1024:
        raise ValidationError('Файл занадто малий або порожній')

def validate_image_dimensions(image):
    """Check image dimensions and aspect ratio (guards against pixel-bomb attacks)."""
    if not image:
        return
    try:
        img = Image.open(image)
        img.verify()
        img.seek(0)
        img = Image.open(image)
        width, height = img.size
    except Exception:
        raise ValidationError("Неправильний формат зображення або файл пошкоджений")

    if width < 100 or height < 100:
        raise ValidationError(f'Мінімальний розмір: 100x100px (ваш: {width}x{height}px)')

    if width > 8000 or height > 8000:
        raise ValidationError(f'Максимальний розмір: 8000x8000px (ваш: {width}x{height}px)')

    # Reject extreme aspect ratios to prevent decompression bomb attacks
    aspect_ratio = max(width, height) / min(width, height)
    if aspect_ratio > 20:
        raise ValidationError('Некоректне співвідношення сторін зображення')


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to="products/%Y/%m/%d/",
        verbose_name="Зображення", 
        blank=True, 
        null=True, 
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif']),
              validate_image_size, validate_image_dimensions
            ]
    )

    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering"]
        verbose_name = "Картинка товару"
        verbose_name_plural = "Картинки товарів"

    def clean(self):
        if self.product and self.product.images.exclude(id=self.id).count() >= 10:
            raise ValidationError(
                "Неможливо додати більше ніж 10 зображень до одного товару."
            )

    def __str__(self):
        product_name = str(self.product)
        return f"{product_name} - Картинка #{self.ordering}"

    def save(self, *args, **kwargs):
        if not self.pk:
            last_ordering = self.product.images.aggregate(
                max_ordering=models.Max("ordering")
            )["max_ordering"]
            self.ordering = (last_ordering or 0) + 1
        super().save(*args, **kwargs)
