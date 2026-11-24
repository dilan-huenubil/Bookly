from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import ACCOUNT_DELETION_GRACE_PERIOD


class Command(BaseCommand):
    help = 'Elimina definitivamente las cuentas cuya eliminación lleva más de 30 días.'

    def handle(self, *args, **options):
        expiration_time = timezone.now() - ACCOUNT_DELETION_GRACE_PERIOD
        expired_users = User.objects.filter(
            profile__deletion_requested_at__isnull=False,
            profile__deletion_requested_at__lte=expiration_time,
        )
        expired_count = expired_users.count()
        expired_users.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'{expired_count} cuenta(s) eliminada(s) definitivamente.'
            )
        )
