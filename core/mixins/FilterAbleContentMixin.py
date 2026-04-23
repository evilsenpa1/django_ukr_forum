from django.db import models
from django.contrib.contenttypes.fields import GenericRelation



class FilterAbleContentMixin(models.Model):
    mediafiles = GenericRelation(
        "mediafiles.MediaFiles",
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name="%(app_label)s_%(class)s_mediafiles"
    )
    tags = models.ManyToManyField(
        "articles.TagsTablModels",
        blank=True,
        help_text="Виберіть теги",
        related_name="%(app_label)s_%(class)s_tags",
    )

    # 3-level geo hierarchy
    country = models.ForeignKey(
        "geo.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Країна",
        related_name="%(app_label)s_%(class)s_country",
    )

    region = models.ForeignKey(
        "geo.Region",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Регіон",
        related_name="%(app_label)s_%(class)s_region",
    )

    city = models.ForeignKey(
        "geo.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Місто",
        related_name="%(app_label)s_%(class)s_city",
    )

    # Конкретне місце (Магазин, кафе, пам'ятка)
    local_place = models.ForeignKey(
        "geo.LocationPlace",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Локація (заклад)",
        related_name="%(app_label)s_%(class)s_place",
    )

    class Meta:
        abstract = True
