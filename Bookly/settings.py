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


SECRET_KEY = 'django-insecure-*lb&9mm8lem06fcp7mn3hkbqv5@mcol2_qk9cm0uii5h2_g#st'
DEBUG = True


ALLOWED_HOSTS = ['127.0.0.1', 'localhost']



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
LOGIN_URL = '/register'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



FLOW_BASE_URL = os.getenv('FLOW_BASE_URL', 'https://sandbox.flow.cl/api')


FLOW_API_KEY = os.getenv('FLOW_API_KEY', 'TU_API_KEY_AQUI') 
FLOW_SECRET = os.getenv('FLOW_SECRET', 'TU_SECRET_KEY_AQUI')



SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'http://localhost:8000').rstrip('/')

# Gmail SMTP. Usa una contraseña de aplicación de Google, no la contraseña
# habitual de la cuenta.
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = (os.getenv('EMAIL_HOST_USER') or '').strip()
# Google muestra la contraseña de aplicación separada por espacios; SMTP
# necesita la clave continua.
EMAIL_HOST_PASSWORD = (os.getenv('EMAIL_HOST_PASSWORD') or '').replace(' ', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
DEFAULT_FROM_EMAIL = (os.getenv('DEFAULT_FROM_EMAIL') or EMAIL_HOST_USER).strip()
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))


SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False 
CSRF_COOKIE_SECURE = False

GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}
