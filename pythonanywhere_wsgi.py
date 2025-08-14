# This is the WSGI configuration file for PythonAnywhere
# Upload this file to /var/www/peepong_pythonanywhere_com_wsgi.py

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/Peepong/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app_simple import app as application