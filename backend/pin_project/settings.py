import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-insecure-change-me-in-production-pin-map-2024')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',  # GeoDjango
    'rest_framework',
    'rest_framework_gis',
    'corsheaders',
    'django_filters',
    'mapapp',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pin_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pin_project.wsgi.application'

# PostgreSQL + PostGIS
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('POSTGRES_DB', 'EXAMPLE'), # ИЗМЕНИТЬ НА ВАШЕ НАЗВАНИЕ БД
        'USER': os.environ.get('POSTGRES_USER', 'EXAMPLE'), # ИЗМЕНИТЬ НА ИМЯ ВАШЕГО ПОЛЬЗОВАТЕЛЯ PSQL
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'EXAMPLE'), # ИЗМЕНИТЬ НА ВАШ ПАРОЛЬ СЕРВЕРА PSQL
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Novokuznetsk'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS for React frontend
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # tighten in production
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# GDAL / GEOS paths (uncomment/adjust if needed on Linux)
# GDAL_LIBRARY_PATH = '/usr/lib/libgdal.so'
# GEOS_LIBRARY_PATH = '/usr/lib/libgeos_c.so'

# ДОБАВИТЬ ВАШ ПУТЬ ДО УСТАНОВЛЕННЫХ БИБЛИОТЕК КАРТОГРАФИИ GDAL, GEOS, PROJ

if os.name == 'nt':
    OSGEO = Path(r'!EXAMPLE!\Here\PIN_map\backend\venv\Lib\site-packages\osgeo')
    PROJ_DIR = OSGEO / 'data' / 'proj'

    os.environ['PATH'] = str(OSGEO) + os.pathsep + os.environ.get('PATH', '')
    os.environ['PROJ_LIB'] = r'!EXAMPLE!\proj_data'
    os.environ['PROJ_DATA'] = r'!EXAMPLE!\proj_data'

    gdal_data = OSGEO / 'data' / 'gdal'
    if gdal_data.exists():
        os.environ['GDAL_DATA'] = str(gdal_data)
    elif (OSGEO / 'data').exists():
        os.environ['GDAL_DATA'] = str(OSGEO / 'data')

    GDAL_LIBRARY_PATH = str(OSGEO / 'gdal.dll')
    GEOS_LIBRARY_PATH = str(OSGEO / 'geos_c.dll')

    