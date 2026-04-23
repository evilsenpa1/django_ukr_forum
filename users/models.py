import random
import string
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.utils.en_de_ref_cod import encode_ref
from geo.models import Country, Region, City
import logging

logger = logging.getLogger(__name__)

class ConsentText(models.Model):
    version = models.CharField(max_length=10, verbose_name="Версія тексту")
    text = models.TextField(verbose_name="Текст погодження")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата створення тексту погодження"
    )

    def __str__(self):
        return f"{self.version}"


def generate_referral_code(length=8):
    """Generate a random alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))

def get_referral_tree(user):
    """Recursively build the tree of users invited by this user.

    WARNING: uses plain recursion — chains deeper than ~100 levels will raise
    RecursionError. Consider migrating to django-mptt if the tree grows large.
    """
    all_referrals = UserReferrals.objects.filter(invitee__isnull=False).select_related('invitee', 'referrer')

    children_map = {}
    for ref in all_referrals:
        children_map.setdefault(ref.referrer_id, []).append(ref.invitee)

    def build(user):
        return [
            {'user': child, 'children': build(child)}
            for child in children_map.get(user.pk, [])
        ]

    return build(user)

class UserReferrals(models.Model):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_sent'
    )
    referral_code = models.CharField(
        max_length=8,
        unique=True,
        blank=True,
        null=True
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='referral_received',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    stop_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)
    referral_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.referrer} -> {self.invitee or 'pending'} ({self.referral_code})"

    class Meta:
        db_table = 'user_referrals'
        verbose_name = 'Власник реф-коду'
        verbose_name_plural = 'Власники реф-коду'

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Save first to get the DB-assigned pk, then encode it into a hashid
        super().save(*args, **kwargs)

        if is_new and not self.referral_code:
            self.referral_code = encode_ref(self.pk)
            # Use update() to avoid triggering save() recursively
            UserReferrals.objects.filter(pk=self.pk).update(referral_code=self.referral_code)
        



class CustomUser(AbstractUser):

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Ваш логін",
        help_text="Обов'язкове поле. Тільки літери, цифри та @/./+/-/_.",
    )

    display_name = models.CharField(
        max_length=100,
        verbose_name="Публічне ім'я (нікнейм)",
        blank=True,
        default="",
    )

    first_name_public = models.BooleanField(default=False)
    last_name_public = models.BooleanField(default=False)

    age = models.PositiveIntegerField(blank=True, null=True, verbose_name="Вік")

    phone_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Телефон"
    )
    phone_public = models.BooleanField(default=False)

    email_public = models.BooleanField(default=False)

    social_network = models.CharField(
        max_length=150, blank=True, null=True, verbose_name="Соц.мережа"
    )
    social_public = models.BooleanField(default=False)

    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Країна",
    )
    country_public = models.BooleanField(default=False)

    region = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Регіон",
    )
    region_public = models.BooleanField(default=False)

    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="Місто",
    )
    city_public = models.BooleanField(default=False)

    consent_given = models.BooleanField(
        default=False, verbose_name="Згода на обробку даних"
    )
    consent_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата згоди"
    )
    consent_version = models.ForeignKey(
        ConsentText, null=True, blank=True, on_delete=models.SET_NULL
    )

    visibility = models.JSONField(default=dict)

    def get_absolute_url(self):
        return reverse("users:user_detail", kwargs={"pk": self.pk})

    def get_full_location(self):
        parts = []
        if self.country:
            country_str = f"{self.country.flag_emoji} {self.country.name}"
            if self.country.currency_symbol:
                country_str += f" ({self.country.currency_symbol})"
            parts.append(country_str)

        if self.region:
            parts.append(self.region.name)

        if self.city:
            parts.append(f"м. {self.city.name}")

        return ", ".join(parts) if parts else "Локація не вказана"

    def save(self, *args, **kwargs):
        # Consent freeze: once given, it cannot be revoked
        if self.pk:
            old_user = CustomUser.objects.get(pk=self.pk)
            if old_user.consent_given:
                self.consent_given = True

        # On first consent, record timestamp and active consent version
        if self.consent_given:
            if not self.consent_date:
                self.consent_date = timezone.now()
            if not self.consent_version:
                latest_consent = ConsentText.objects.order_by("-created_at").first()
                if latest_consent:
                    self.consent_version = latest_consent
        super().save(*args, **kwargs)

    def get_public_name(self):
        return self.display_name or self.username

    def get_public_first_name(self):
        if self.first_name_public:
            return self.first_name
        return None

    def get_public_last_name(self):
        if self.last_name_public:
            return self.last_name
        return None

    def get_public_email(self):
        if self.email_public:
            return self.email
        return None

    def get_public_phone(self):
        if self.phone_public:
            return self.phone_number
        return None

    def get_public_social(self):
        if self.social_public:
            return self.social_network
        return None

    def get_public_country(self):
        if self.country_public and self.country:
            return self.country.name
        return None

    def get_public_region(self):
        logger.debug("region=%s, public=%s", self.region, self.region_public)
        if self.region_public and self.region:
            return self.region
        return None

    def get_public_city(self):
        if self.city_public and self.city:
            return self.city.name
        return None

    @property
    def verbose_names(self):
        return {
            f.name: f.verbose_name
            for f in self._meta.get_fields()
            if hasattr(f, "verbose_name")
        }
