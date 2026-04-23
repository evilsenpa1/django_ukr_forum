from django.db import models
from django.urls import reverse
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва країни")
    name_translate=models.CharField(max_length=100,default="",blank=True, null=True,verbose_name="Назва країни українською")
    code = models.CharField(
        max_length=22, unique=True, verbose_name="Код (ISO 3166-1 alpha-2)"
    )
    flag_emoji = models.CharField(
        max_length=10, blank=True, verbose_name="Емодзі прапора"
    )
    currency = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Валюта"
    )
    currency_symbol = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Символ валюти"
    )

    class Meta:
        db_table = "geo_country"
        verbose_name = "Країна"
        verbose_name_plural = "Країни"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} {self.flag_emoji}".strip()

    def save(self, *args, **kwargs):
        # Generate flag emoji from 2-letter ISO code (e.g. 'UA' → '🇺🇦')
        if self.code and not self.flag_emoji:
            code = self.code.upper()
            if len(code) == 2 and all('A' <= c <= 'Z' for c in code):
                self.flag_emoji = "".join(chr(127462 + ord(c) - 65) for c in code)

        # Fetch currency from CountryStateCity API on first save
        if not self.currency and self.code:
            api_key = getattr(settings, 'COUNTRY_STATE_CITY_API_KEY', None)
            base_url = getattr(settings, 'BASE_URL_COUNTRY_STATE_CITY', "https://api.countrystatecity.in/v1")

            if api_key:
                headers = {'X-CSCAPI-KEY': api_key}
                try:
                    response = requests.get(f"{base_url}/countries/{self.code.upper()}", headers=headers, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        self.currency = data.get('currency')
                        self.currency_symbol = data.get('currency_symbol') or data.get('currency_char')
                except Exception as e:
                    logger.debug("API error fetching currency: %s", e)

        super().save(*args, **kwargs)

class Region(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва регіону")
    name_translate=models.CharField(max_length=100,default="",blank=True, null=True,verbose_name="Назва регіону українською")
    state_code = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Код регіону (ISO/FIPS)"
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="regions",
        verbose_name="Назва країни",
    )

    class Meta:
        db_table = "geo_region"
        verbose_name = "Регіон"
        verbose_name_plural = "Регіони"
        unique_together = ("name", "country")
        ordering = ["country__name", "name"]

    def __str__(self):
        return f"{self.name} "  # ({self.country.name})


class City(models.Model):
    name = models.CharField(max_length=255, verbose_name="Назва міста")
    name_translate=models.CharField(max_length=255,default="",blank=True, null=True,verbose_name="Назва міста українською")
 
    city_id = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        verbose_name="Зовнішній ID (наприклад, GeoNames)",
    )
    latitude = models.DecimalField(
        max_digits=20, decimal_places=16, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=20, decimal_places=16, null=True, blank=True
    )

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cities",
        verbose_name="Назва країни",
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="cities",
        verbose_name="Назва регіону",
    )

    class Meta:
        db_table = "geo_city"
        verbose_name = "Місто"
        verbose_name_plural = "Міста"
        # unique_together = ('name','region')
        ordering = ["country__name", "region__name", "name"]

    def __str__(self):
        return f"{self.name} "  # ({self.region.name},{self.country.name})

    def save(self, *args, **kwargs):
        if self.region_id and not self.country_id:
            self.country = self.region.country
        elif self.country_id and self.region_id and self.region.country_id != self.country_id:
            raise ValueError("Регіон належить до іншої країни")
        super().save(*args, **kwargs)


class LocationPlace(models.Model):
    place_name = models.CharField(max_length=255, verbose_name="Назва або опис місця")
    # Null when the user clicks an arbitrary map point instead of selecting a place
    place_id = models.CharField(max_length=255, unique=True, null=True, blank=True, verbose_name="Google Place ID")
    latitude = models.DecimalField(max_digits=20, null=True, decimal_places=16, verbose_name="Широта")
    longitude = models.DecimalField(max_digits=20, null=True, decimal_places=16, verbose_name="Довгота")

    class Meta:
        db_table = "geo_location_place"
        verbose_name = "Мітка на карті"
        verbose_name_plural = "Мітки на карті"

    def __str__(self):
        return self.place_name