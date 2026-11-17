import random
import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from core.models import Book, Order, OrderItem


SEASONAL_DEMAND_WEIGHTS = {
    1: 0.7,
    2: 0.45,
    3: 0.8,
    4: 0.9,
    5: 1.0,
    6: 1.1,
    7: 1.0,
    8: 0.85,
    9: 1.0,
    10: 1.2,
    11: 2.8,
    12: 3.0,
}


def _seasonal_created_at(start, end):
    day_count = (end - start).days
    candidate_days = [
        start + timedelta(days=day_offset)
        for day_offset in range(day_count + 1)
    ]
    weights = [
        SEASONAL_DEMAND_WEIGHTS[created_at.month]
        for created_at in candidate_days
    ]
    selected_day = random.choices(candidate_days, weights=weights, k=1)[0]
    available_seconds = min(
        23 * 60 * 60 + 59 * 60 + 59,
        int((end - selected_day).total_seconds()),
    )
    return selected_day + timedelta(
        seconds=random.randint(0, max(0, available_seconds)),
    )


class Command(BaseCommand):
    help = (
        'Genera pedidos ficticios asociados a libros, usuarios y fechas '
        'de los últimos 6 a 12 meses.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            help='Cantidad de pedidos a generar (por defecto, un valor entre 50 y 100).',
        )

    def handle(self, *args, **options):
        count = options.get('count') or random.randint(50, 100)
        if not 50 <= count <= 100:
            raise CommandError('La cantidad debe estar entre 50 y 100.')

        books = list(Book.objects.all())
        users = list(User.objects.all())
        if not books:
            raise CommandError('No hay libros disponibles para asociar los pedidos.')
        if not users:
            raise CommandError('No hay usuarios disponibles para asociar los pedidos.')

        now = timezone.now()
        start = now - timedelta(days=365)
        end = now - timedelta(days=180)
        created_orders = []

        with transaction.atomic():
            for _ in range(count):
                selected_items = random.sample(
                    books,
                    k=random.randint(1, min(3, len(books))),
                )
                order_items = []
                total = 0
                for book in selected_items:
                    quantity = random.randint(1, 4)
                    total += book.price * quantity
                    order_items.append((book, quantity))

                state = random.choice(('paid', 'en_camino', 'canceled'))
                status = 'canceled' if state == 'canceled' else 'paid'
                tracking_status = 'en_camino' if state == 'en_camino' else (
                    'entregado' if status == 'paid' else 'preparando'
                )
                user = random.choice(users)
                order = Order.objects.create(
                    user=user,
                    commerce_order=f'SEED-{uuid.uuid4().hex[:24].upper()}',
                    amount=total,
                    currency='CLP',
                    email=user.email or 'seed@bookly.local',
                    first_item_title=order_items[0][0].title,
                    status=status,
                    tracking_status=tracking_status,
                    confirmation_reached=status == 'paid',
                    stock_updated=False,
                )
                created_at = _seasonal_created_at(start, end)
                Order.objects.filter(pk=order.pk).update(
                    created_at=created_at,
                    updated_at=created_at,
                )
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        book=book,
                        quantity=quantity,
                        price_at_purchase=book.price,
                    )
                    for book, quantity in order_items
                ])
                created_orders.append(order)

        self.stdout.write(
            self.style.SUCCESS(
                f'{len(created_orders)} pedidos ficticios generados correctamente.'
            )
        )
