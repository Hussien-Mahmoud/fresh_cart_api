"""
Django settings for fresh_cart project configured for async Django-Ninja API, Postgres, and Docker/Nginx.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]
# CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if os.getenv('USE_SECURE_PROXY_SSL_HEADER', 'true').lower() == 'true' else None
# USE_X_FORWARDED_HOST = True

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'ninja',
    'ninja_jwt',
    'ninja_extra',
    'cloudinary',
    'cloudinary_storage',

    # Local apps
    'catalog',
    'users',
    'carts',
    'orders',
    'payments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'ninja.compatibility.files.fix_request_files_middleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fresh_cart.urls'

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

# ASGI (async) application
ASGI_APPLICATION = 'fresh_cart.asgi.application'

# Database - PostgreSQL
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
        'OPTIONS': dict(parse_qsl(tmpPostgres.query)),
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('POSTGRES_DB'),
#         'USER': os.getenv('POSTGRES_USER'),
#         'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
#         'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
#         'PORT': os.getenv('POSTGRES_PORT', '5432'),
#     }
# }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Storage for media uploads
# if os.getenv('USE_CLOUDINARY', 'true').lower() == 'true':
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

CLOUDINARY_URL = os.getenv('CLOUDINARY_URL', '')
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
    'SECURE': True,
    'OVERWRITE': False,
    'RESOURCE_TYPES': ['image', 'video', 'raw'],
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@freshcart.local')

# Stripe
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')


from datetime import timedelta
NINJA_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),  # Access tokens expire in 60 minutes
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # Refresh tokens expire in 7 days
}

AUTH_USER_MODEL = 'users.User'

# Logging configuration for SQL queries
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'sql': {
                'format': '[%(duration).3f] %(sql)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'sql_console': {
                'class': 'logging.StreamHandler',
                'formatter': 'sql',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['sql_console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }

# Redis Cache
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379')
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}
