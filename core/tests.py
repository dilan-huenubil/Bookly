from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone
from unittest.mock import patch

from .models import Book, BookRecommendation, Order, OrderItem, Profile


class AdminBookManualCreationTests(TestCase):
    def test_admin_book_form_has_no_feria_import(self):
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='ValidPassword1!',
        )
        self.client.force_login(admin)

        response = self.client.get('/admin/libros/')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'bookImportUrl')
        self.assertNotContains(response, 'Completar datos')
        self.assertNotContains(response, 'Feria Chilena del Libro')

    def test_admin_can_filter_inactive_books(self):
        admin = User.objects.create_superuser(
            username='inactive-admin',
            email='inactive-admin@example.com',
            password='ValidPassword1!',
        )
        active_book = Book.objects.create(
            title='Libro activo',
            author='Autor activo',
            sku='ACTIVE-001',
            price=10000,
            is_active=True,
        )
        inactive_book = Book.objects.create(
            title='Libro desactivado',
            author='Autor desactivado',
            sku='INACTIVE-001',
            price=12000,
            is_active=False,
        )
        self.client.force_login(admin)

        response = self.client.get('/admin/libros/?status=inactive')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ver todos')
        self.assertContains(response, 'Libro desactivado')
        self.assertNotContains(response, 'Libro activo')

    def test_admin_can_bulk_deactivate_books(self):
        admin = User.objects.create_superuser(
            username='bulk-admin',
            email='bulk-admin@example.com',
            password='ValidPassword1!',
        )
        first = Book.objects.create(
            title='Primer libro',
            author='Autor uno',
            sku='BULK-001',
            price=10000,
            is_active=True,
        )
        second = Book.objects.create(
            title='Segundo libro',
            author='Autor dos',
            sku='BULK-002',
            price=12000,
            is_active=True,
        )
        third = Book.objects.create(
            title='Tercer libro',
            author='Autor tres',
            sku='BULK-003',
            price=14000,
            is_active=True,
        )
        self.client.force_login(admin)

        response = self.client.post('/admin/libros/desactivar-varios/', {
            'book_ids': [first.pk, second.pk],
            'status': 'all',
        })

        self.assertRedirects(
            response,
            '/admin/libros/?status=all',
            fetch_redirect_response=False,
        )
        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertFalse(first.is_active)
        self.assertFalse(second.is_active)
        self.assertTrue(third.is_active)

    def test_admin_can_bulk_activate_inactive_books(self):
        admin = User.objects.create_superuser(
            username='bulk-activate-admin',
            email='bulk-activate-admin@example.com',
            password='ValidPassword1!',
        )
        first = Book.objects.create(
            title='Libro inactivo uno',
            author='Autor uno',
            sku='ACTIVATE-001',
            price=10000,
            is_active=False,
        )
        second = Book.objects.create(
            title='Libro inactivo dos',
            author='Autor dos',
            sku='ACTIVATE-002',
            price=12000,
            is_active=False,
        )
        third = Book.objects.create(
            title='Libro activo',
            author='Autor tres',
            sku='ACTIVATE-003',
            price=14000,
            is_active=True,
        )
        self.client.force_login(admin)

        response = self.client.post('/admin/libros/desactivar-varios/', {
            'book_ids': [first.pk, second.pk],
            'status': 'inactive',
            'action': 'activate',
        })

        self.assertRedirects(
            response,
            '/admin/libros/?status=inactive',
            fetch_redirect_response=False,
        )
        first.refresh_from_db()
        second.refresh_from_db()
        third.refresh_from_db()
        self.assertTrue(first.is_active)
        self.assertTrue(second.is_active)
        self.assertTrue(third.is_active)


class AdminOrderNavigationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='order-admin',
            email='order-admin@example.com',
            password='ValidPassword1!',
        )
        self.user = User.objects.create_user(
            username='order-user',
            email='order-user@example.com',
            password='ValidPassword1!',
        )
        self.order = Order.objects.create(
            user=self.user,
            commerce_order='ORD-NAV-001',
            amount=10000,
            email=self.user.email,
        )
        self.client.force_login(self.admin)

    def test_cancel_modal_replaces_edit_url_with_admin_orders_url(self):
        response = self.client.get(f'/admin/pedidos/{self.order.pk}/editar/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-list-url="/admin/pedidos/"')
        self.assertContains(response, "window.history.replaceState")

    def test_search_and_pagination_keep_admin_orders_route(self):
        response = self.client.get(f'/admin/pedidos/{self.order.pk}/editar/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/admin/pedidos/"')
        self.assertNotContains(
            response,
            'href="?q=',
        )

    def test_order_delete_uses_sweetalert_confirmation(self):
        response = self.client.get('/admin/pedidos/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="delete-order-form"')
        self.assertContains(response, '¿Estás seguro de eliminar esta orden de compra?')
        self.assertContains(response, 'La orden de compra fue eliminada correctamente.')
        self.assertContains(response, 'confirmButtonText: "OK"')
        self.assertContains(response, 'icon: "success"')
        self.assertNotContains(response, "confirm('¿Eliminar este pedido?")


class CheckoutAuthenticationTests(TestCase):
    def test_cart_page_has_checkout_button(self):
        user = User.objects.create_user(
            username='comprador_carrito',
            email='comprador-carrito@example.com',
            password='ValidPassword1!',
        )
        self.client.force_login(user)

        response = self.client.get('/carrito/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/checkout/"')

    def test_checkout_redirects_anonymous_user_to_login(self):
        response = self.client.get('/checkout/')

        self.assertRedirects(
            response,
            '/login/?next=/checkout/',
            fetch_redirect_response=False,
        )

    def test_cart_checkout_redirect_target_returns_to_cart_after_login(self):
        user = User.objects.create_user(
            username='comprador',
            email='comprador@example.com',
            password='ValidPassword1!',
        )

        response = self.client.post('/login/', {
            'form_type': 'login',
            'username': user.username,
            'password': 'ValidPassword1!',
            'next': '/carrito/',
        })

        self.assertRedirects(
            response,
            '/carrito/',
            fetch_redirect_response=False,
        )

    def test_login_page_renders_login_form_not_registration(self):
        response = self.client.get('/login/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="loginForm"', html=False)
        self.assertNotContains(response, 'id="registerForm"', html=False)


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
    @patch('core.views.requests.get')
    def test_flow_return_marks_order_paid_and_redirects_cleanly(self, mock_get):
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

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'status': 2,
            'flowOrder': 'FLOW-TEST-001',
        }

        response = self.client.get('/flow/return/?token=flow-token-test')

        self.assertRedirects(response, '/confirmacion_pedido/', fetch_redirect_response=False)
        self.assertEqual(
            self.client.session['ultima_orden_id'],
            order.id,
        )
        self.assertTrue(
            self.client.session.get('_auth_user_id'),
        )

        response = self.client.get('/confirmacion_pedido/')
        self.assertEqual(response.status_code, 200, response.get('Location'))
        order.refresh_from_db()
        book.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.tracking_status, 'solicitud_compra')
        self.assertTrue(order.confirmation_reached)
        self.assertTrue(order.stock_updated)
        self.assertEqual(book.stock, 1)

    def test_confirmation_rejects_order_from_another_user(self):
        owner = User.objects.create_user(
            username='dueno',
            password='ValidPassword1!',
        )
        other = User.objects.create_user(
            username='otro',
            password='ValidPassword1!',
        )
        order = Order.objects.create(
            user=owner,
            commerce_order='ORD-TEST-OWNER',
            amount=10000,
            email=owner.email,
        )

        self.client.force_login(other)
        session = self.client.session
        session['ultima_orden_id'] = order.id
        session.save()

        response = self.client.get('/confirmacion_pedido/')

        self.assertEqual(response.status_code, 403)


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
