from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q  # Importación clave para combinar consultas

from .models import ACCOUNT_DELETION_GRACE_PERIOD

class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        UserModel = get_user_model()

        try:
            username_field = f"{UserModel.USERNAME_FIELD}__iexact"
            # OPTIMIZACIÓN: 1 solo viaje a Aiven. 
            # Trae al usuario (por nombre o email) y también adjunta su perfil de una vez.
            user = UserModel._default_manager.select_related('profile').filter(
                Q(**{username_field: username}) | Q(email__iexact=username)
            ).first()
        except Exception:
            return None

        # Si el usuario no existe, cortamos el proceso de inmediato
        if not user:
            return None

        # Como usamos select_related, pedir el profile ya no genera otra consulta a la base de datos
        pending_deletion_at = getattr(getattr(user, 'profile', None), 'deletion_requested_at', None)
        if (
            pending_deletion_at is not None
            and timezone.now() >= pending_deletion_at + ACCOUNT_DELETION_GRACE_PERIOD
        ):
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
            
        return None