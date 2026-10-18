from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from django.utils import timezone

from .models import Profile


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

# Create your tests here.
