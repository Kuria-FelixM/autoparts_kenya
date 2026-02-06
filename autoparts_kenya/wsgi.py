"""
WSGI config for AutoParts Kenya project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoparts_kenya.settings')
application = get_wsgi_application()
