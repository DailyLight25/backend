"""
Django management command to clean up expired unverified users.
Run this periodically (e.g., via cron) to keep the database clean.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User


class Command(BaseCommand):
    help = 'Deletes expired unverified users from the database'

    def handle(self, *args, **options):
        # Find all unverified users whose verification has expired
        expired_users = User.objects.filter(
            is_verified=False,
            verification_expires_at__lt=timezone.now()
        )
        
        count = expired_users.count()
        
        if count > 0:
            expired_users.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} expired unverified user(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('No expired unverified users to delete')
            )

