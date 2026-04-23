"""
Management command to create a dev superuser (admin/admin) if one does not exist.
Intended for use in Docker dev environment only — do NOT run in production.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create dev superuser admin/admin (idempotent, skips if already exists)"

    def handle(self, *args, **options):
        User = get_user_model()
        username = "admin"
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists, skipping."))
            return
        User.objects.create_superuser(username=username, email="admin@example.com", password="admin")
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created (password: admin)."))
