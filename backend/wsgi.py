"""
WSGI config for ISM project.

cPanel deployment entry point.
"""

import os
import sys

# Add project directory to Python path for cPanel
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ism_project.settings')

# Apply virtualenv if exists
venv_path = os.path.join(project_root, '.venv')
if os.path.exists(venv_path):
    site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
    sys.path.insert(0, site_packages)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()