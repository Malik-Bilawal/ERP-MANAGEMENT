import os
import mimetypes
from pathlib import Path
from dotenv import load_dotenv

# Fix for Windows: Ensures CSS/JS files are served with correct headers
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/javascript", ".js", True)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-qfl86rm2_+3s&v+7^yk#=bfap+@*nr^5_$61a)65(brev@v$o@'

DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "unfold",  # MUST stay at the top
    "unfold.contrib.filters",
    "unfold.contrib.import_export",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    "rest_framework",
    "corsheaders",
    "rangefilter",
    "core",
    "services",  # Add this line
    "client_management",  # Add this
    "financial",  # Add this



   

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"], 
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

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'srf_ims_db',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3308',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Static & Media Files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static'

STATICFILES_DIRS = [] 

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
UNFOLD = {
    # ... previous settings ...
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "icon": "dashboard",
                "items": [
                    {"title": "Financial Dashboard", "link": "/admin/financial/financialsummary/", "icon": "analytics"},
                ],
            },
            {
                "title": "Client Management",
                "icon": "people",
                "items": [
                    {"title": "Clients", "link": "/admin/client_management/client/", "icon": "person"},
                    {"title": "Projects", "link": "/admin/client_management/project/", "icon": "work"},
                    {"title": "Time Entries", "link": "/admin/client_management/timeentry/", "icon": "schedule"},
                    {"title": "Milestones", "link": "/admin/client_management/milestone/", "icon": "flag"},
                    {"title": "Documents", "link": "/admin/client_management/clientdocument/", "icon": "folder"},
                    {"title": "Communications", "link": "/admin/client_management/clientcommunication/", "icon": "chat"},
                ],
            },
            {
                "title": "Financial Management",
                "icon": "payments",
                "items": [
                    {"title": "Invoices", "link": "/admin/financial/invoice/", "icon": "receipt"},
                    {"title": "Revenue", "link": "/admin/financial/revenue/", "icon": "trending_up"},
                    {"title": "Client Balances", "link": "/admin/financial/clientbalance/", "icon": "account_balance"},
                    {"title": "Company Revenue", "link": "/admin/financial/companyrevenue/", "icon": "summarize"},
                ],
           },
            {
                "title": "Services Management",
                "icon": "services",
                "items": [
                    {"title": "Service Categories", "link": "/admin/services/servicecategory/", "icon": "category"},
                    {"title": "Services", "link": "/admin/services/service/", "icon": "build"},
                    {"title": "Sub-Services", "link": "/admin/services/subservice/", "icon": "list_alt"},
                    {"title": "Client Services", "link": "/admin/services/clientservice/", "icon": "people"},
                    {"title": "Pricing History", "link": "/admin/services/servicepricinghistory/", "icon": "history"},
                ],
            },
            {
                "title": "System Settings",
                "icon": "settings",
                "items": [
                    {"title": "Company Settings", "link": "/admin/core/companysettings/", "icon": "business"},
                ],
            },
        ],
    },
}

# Extra fixes
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication', 
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}