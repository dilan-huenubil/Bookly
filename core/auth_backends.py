from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ACCOUNT_DELETION_GRACE_PERIOD


class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        UserModel = get_user_model()

        user = None
        try:
            username_field = f"{UserModel.USERNAME_FIELD}__iexact"
            user = (
                UserModel._default_manager.filter(**{username_field: username}).first()
                or UserModel._default_manager.filter(email__iexact=username).first()
            )
        except Exception:
            return None

        pending_deletion_at = getattr(getattr(user, 'profile', None), 'deletion_requested_at', None)
        if (
            pending_deletion_at is not None
            and timezone.now() >= pending_deletion_at + ACCOUNT_DELETION_GRACE_PERIOD
        ):
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None