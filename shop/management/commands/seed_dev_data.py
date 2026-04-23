"""
Management command to seed initial shop dev data.
Creates a test category if it does not already exist.
Intended for use in Docker dev environment only — do NOT run in production.
"""

from django.core.management.base import BaseCommand

from shop.models import Categories


class Command(BaseCommand):
    help = "Seed dev shop data: creates a test category (idempotent)"

    def handle(self, *args, **options):
        name = "Тест"
        slug = "test"
        _, created = Categories.objects.get_or_create(
            slug=slug,
            defaults={"name": name},
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Category '{name}' created."))
        else:
            self.stdout.write(self.style.WARNING(f"Category with slug '{slug}' already exists, skipping."))
