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
    "clients",
    "projects",
    "payments",
    # New apps for staff management
    "staff",  # For company staff management
    "assignments",  # For project assignments to staff
    "salary",  # For staff salary and invoice management
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
        'PASSWORD': 'admin123',
        'HOST': 'localhost',
        'PORT': '3307',
        'OPTIONS': {
            # This forces Django to treat the DB as an older version
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
    "SITE_TITLE": "SRF Integrated Management System",
    "SITE_HEADER": "SRF IMS",
    "SITE_URL": "/",
    "COLORS": {
        "primary": {
            "50": "#eff6ff", "100": "#dbeafe", "200": "#bfdbfe",
            "300": "#93c5fd", "400": "#60a5fa", "500": "#3b82f6",
            "600": "#2563eb", "700": "#1d4ed8", "800": "#1e40af",
            "900": "#1e3a8a", "950": "#172554",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": True,
                "items": [
                    {"title": "Analytics Dashboard", "icon": "dashboard", "link": "/admin/dashboard/"},
                ],
            },
            {
                "title": "Business Operations",
                "separator": True,
                "items": [
                    {"title": "Clients", "icon": "groups", "link": "/admin/clients/client/"},
                    {"title": "Projects", "icon": "rocket_launch", "link": "/admin/projects/project/"},
                    {"title": "Payments & Invoices", "icon": "account_balance_wallet", "link": "/admin/payments/payment/"},
                ],
            },
            # Staff Management Section (consolidated)
            {
                "title": "Staff Management",
                "separator": True,
                "items": [
                    {"title": "Staff Members", "icon": "badge", "link": "/admin/staff/staff/"},
                    {"title": "Staff Roles", "icon": "assignment_ind", "link": "/admin/staff/role/"},
                    {"title": "Project Assignments", "icon": "assignment", "link": "/admin/assignments/assignment/"},
                ],
            },
            # Salary & Finance Section
            {
                "title": "Salary & Finance",
                "separator": True,
                "items": [
                    {"title": "Salary Structures", "icon": "account_tree", "link": "/admin/salary/salarystructure/"},
                    {"title": "Salary Assignments", "icon": "assignment", "link": "/admin/salary/salaryassignment/"},
                    {"title": "Salary Slips", "icon": "receipt", "link": "/admin/salary/salaryslip/"},
                    {"title": "Staff Invoices", "icon": "receipt_long", "link": "/admin/salary/staffinvoice/"},
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