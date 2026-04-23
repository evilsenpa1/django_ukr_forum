from django.core.management.base import BaseCommand
from django_countries import countries
from geo.models import Country

SELECTED = [
    "GB", "UA", "KZ", "US", "CA", "IL", "KR", "CN", "JP",
    "AU", "TR", "AE", "IN", "VN", "TH", "PH", "NZ", "MN",
    "AZ", "GE",
    # ЕС
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR","HU","IE","IT",
    "LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE",
    # Балканы
    "AL","BA","ME","MK","RS","XK"
]

class Command(BaseCommand):
    help = "Seed selected countries with name, code and flag"

    def handle(self, *args, **options):
        created = 0
        for code in SELECTED:
            try:
                name = countries.name(code)  # вот тут исправлено
            except KeyError:
                self.stdout.write(self.style.WARNING(f"Country code {code} not found in django-countries"))
                continue

            obj, is_created = Country.objects.get_or_create(
                country_code=code,
                defaults={
                    'country_name': name
                }
            )
            if is_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Added {created} countries"))
