from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from .models import Book, BookRecommendation, Order, OrderItem, Profile


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.password = 'ValidPassword1!'
        self.user = User.objects.create_user(
            username='usuario',
            email='usuario@example.com',
            password=self.password,
        )
        self.client = Client()

    def test_account_can_be_marked_for_deletion(self):
        self.client.force_login(self.user)

        response = self.client.post('/mi-cuenta/eliminar/')

        self.assertRedirects(response, '/')
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.profile.deletion_requested_at)

    def test_login_restores_account_within_grace_period(self):
        self.user.profile.deletion_requested_at = timezone.now() - timedelta(days=29)
        self.user.profile.save(update_fields=['deletion_requested_at'])

        response = self.client.post('/login/', {
            'form_type': 'login',
            'username': self.user.username,
            'password': self.password,
        })

        self.assertRedirects(response, '/')
        self.user.profile.refresh_from_db()
        self.assertIsNone(self.user.profile.deletion_requested_at)

    def test_expired_account_cannot_authenticate(self):
        self.user.profile.deletion_requested_at = timezone.now() - timedelta(days=30, seconds=1)
        self.user.profile.save(update_fields=['deletion_requested_at'])

        self.assertIsNone(authenticate(
            username=self.user.username,
            password=self.password,
        ))

    def test_cleanup_deletes_expired_accounts(self):
        self.user.profile.deletion_requested_at = timezone.now() - timedelta(days=31)
        self.user.profile.save(update_fields=['deletion_requested_at'])

        call_command('cleanup_deleted_accounts')

        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())


class OrderConfirmationTests(TestCase):
    def test_confirmation_marks_created_order_as_paid(self):
        user = User.objects.create_user(
            username='comprador',
            email='comprador@example.com',
            password='ValidPassword1!',
        )
        book = Book.objects.create(
            title='Libro de prueba',
            author='Autor de prueba',
            sku='TEST-BOOK-001',
            price=10000,
            stock=2,
        )
        order = Order.objects.create(
            user=user,
            commerce_order='ORD-TEST-001',
            flow_token='flow-token-test',
            amount=13990,
            email=user.email,
        )
        OrderItem.objects.create(
            order=order,
            book=book,
            quantity=1,
            price_at_purchase=book.price,
        )

        response = self.client.get('/confirmacion_pedido/?token=flow-token-test')

        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        book.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertTrue(order.confirmation_reached)
        self.assertTrue(order.stock_updated)
        self.assertEqual(book.stock, 1)


class HomeRecommendationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='recomendaciones',
            password='ValidPassword1!',
        )
        self.purchased_book = Book.objects.create(
            title='Libro comprado',
            author='Autor',
            sku='PURCHASED-001',
            category='Novela',
            price=10000,
            stock=1,
        )
        order = Order.objects.create(
            user=self.user,
            commerce_order='ORD-RECOMMENDATIONS-001',
            amount=10000,
            email='recomendaciones@example.com',
            status='paid',
        )
        OrderItem.objects.create(
            order=order,
            book=self.purchased_book,
            quantity=1,
            price_at_purchase=self.purchased_book.price,
        )

    def test_recommendations_are_limited_to_purchased_categories(self):
        matching = Book.objects.create(
            title='Novela recomendada',
            author='Autor',
            sku='MATCHING-001',
            category='Novela',
            price=10000,
            stock=1,
        )
        different_category = Book.objects.create(
            title='Ensayo recomendado',
            author='Autor',
            sku='DIFFERENT-001',
            category='Ensayo',
            price=10000,
            stock=1,
        )
        BookRecommendation.objects.create(
            book=self.purchased_book,
            recommended_book=matching,
            score=0.8,
            rank=1,
        )
        BookRecommendation.objects.create(
            book=self.purchased_book,
            recommended_book=different_category,
            score=1.0,
            rank=2,
        )

        self.client.force_login(self.user)
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['recommendations']),
            [matching],
        )
        self.assertEqual(
            response.context['section_title'],
            'Basado en tus compras recientes',
        )

    def test_fallback_fills_recommendations_from_purchased_categories(self):
        matching = Book.objects.create(
            title='Novela recomendada',
            author='Autor',
            sku='MATCHING-002',
            category='Novela',
            price=10000,
            stock=1,
        )
        fallback = [
            Book.objects.create(
                title=f'Novela de relleno {index}',
                author='Autor',
                sku=f'FALLBACK-{index:03d}',
                category='Novela',
                price=10000,
                stock=1,
            )
            for index in range(1, 4)
        ]
        BookRecommendation.objects.create(
            book=self.purchased_book,
            recommended_book=matching,
            score=0.8,
            rank=1,
        )

        self.client.force_login(self.user)
        response = self.client.get('/')

        recommendations = response.context['recommendations']
        self.assertEqual(len(recommendations), 4)
        self.assertEqual(
            {book.category for book in recommendations},
            {'Novela'},
        )
        self.assertNotIn(self.purchased_book, recommendations)
        self.assertEqual(
            {book.pk for book in recommendations},
            {matching.pk, *(book.pk for book in fallback)},
        )

    def test_same_recommendation_from_multiple_purchases_is_shown_once(self):
        second_purchased_book = Book.objects.create(
            title='Segundo libro comprado',
            author='Autor',
            sku='PURCHASED-002',
            category='Novela',
            price=10000,
            stock=1,
        )
        second_order = Order.objects.create(
            user=self.user,
            commerce_order='ORD-RECOMMENDATIONS-002',
            amount=10000,
            email='recomendaciones@example.com',
            status='paid',
        )
        OrderItem.objects.create(
            order=second_order,
            book=second_purchased_book,
            quantity=1,
            price_at_purchase=second_purchased_book.price,
        )
        matching = Book.objects.create(
            title='Recomendación compartida',
            author='Autor',
            sku='SHARED-001',
            category='Novela',
            price=10000,
            stock=1,
        )
        BookRecommendation.objects.create(
            book=self.purchased_book,
            recommended_book=matching,
            score=0.8,
            rank=1,
        )
        BookRecommendation.objects.create(
            book=second_purchased_book,
            recommended_book=matching,
            score=0.9,
            rank=1,
        )

        self.client.force_login(self.user)
        response = self.client.get('/')

        recommendations = response.context['recommendations']
        self.assertEqual(
            [book.pk for book in recommendations].count(matching.pk),
            1,
        )


# Create your tests here.
