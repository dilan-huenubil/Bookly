from django.core.management.base import BaseCommand

from core.views import cancel_expired_orders


class Command(BaseCommand):
    help = 'Cancela pedidos sin pago después de 15 minutos.'

    def handle(self, *args, **options):
        canceled_count = cancel_expired_orders()
        self.stdout.write(
            self.style.SUCCESS(
                f'{canceled_count} pedido(s) pendiente(s) cancelado(s).'
            )
        )
