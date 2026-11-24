from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

def _load_dotenv(path: Path):
    try:
        if not path.exists():
            return
        for raw in path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)
    except Exception:
        pass


_load_dotenv(BASE_DIR / '.env')


# ─── Entorno ───────────────────────────────────────────────────────
# En Render configurar la variable DJANGO_ENV=production
IS_PRODUCTION = os.environ.get('DJANGO_ENV') == 'production'

# W009: Clave secreta segura (se lee del .env o variable de entorno)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# W018: DEBUG apagado en producción
DEBUG = not IS_PRODUCTION

ALLOWED_HOSTS = ['bookly-6dsb.onrender.com', 'localhost', '127.0.0.1']



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
    'anymail',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Bookly.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.book_categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'Bookly.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'ssl': {'ssl_mode': 'REQUIRED'},
        },
        'CONN_MAX_AGE': 60,
    }
}


AUTHENTICATION_BACKENDS = [
    'core.auth_backends.UsernameOrEmailBackend',
]



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True



STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



FLOW_BASE_URL = os.getenv('FLOW_BASE_URL', 'https://sandbox.flow.cl/api')


FLOW_API_KEY = os.getenv('FLOW_API_KEY', 'TU_API_KEY_AQUI') 
FLOW_SECRET = os.getenv('FLOW_SECRET', 'TU_SECRET_KEY_AQUI')



SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'http://localhost:8000').rstrip('/')

# Configuración de Anymail con Brevo (Sendinblue) API.
EMAIL_BACKEND = 'anymail.backends.sendinblue.EmailBackend'
ANYMAIL = {
    'SENDINBLUE_API_KEY': os.getenv('BREVO_API_KEY'),
}
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')


# ─── Seguridad SSL / Cookies (solo producción) ────────────────────
SESSION_COOKIE_SAMESITE = 'Lax'

# W012 y W016: Cookies seguras solo con HTTPS
SESSION_COOKIE_SECURE = IS_PRODUCTION
CSRF_COOKIE_SECURE = IS_PRODUCTION

# W008: Redirección HTTP → HTTPS
SECURE_SSL_REDIRECT = IS_PRODUCTION

# W004: HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000 if IS_PRODUCTION else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = IS_PRODUCTION
SECURE_HSTS_PRELOAD = IS_PRODUCTION

GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}
