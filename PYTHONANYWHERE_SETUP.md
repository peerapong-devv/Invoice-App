# PythonAnywhere Deployment Instructions

## Steps to Fix the Error

### 1. Upload Files to PythonAnywhere
Upload these files from your `backend/` folder to `/home/Peepong/mysite/`:
- app_simple.py
- final_improved_tiktok_parser_v2.py
- google_parser_professional.py
- facebook_parser_complete.py

### 2. Update WSGI Configuration
Replace the content of `/var/www/peepong_pythonanywhere_com_wsgi.py` with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/Peepong/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app_simple import app as application
```

### 3. Install Required Packages
In PythonAnywhere console, run:
```bash
pip install --user Flask flask-cors PyMuPDF
```

### 4. Reload Web App
Go to the Web tab in PythonAnywhere and click "Reload" button.

## File Structure on PythonAnywhere
```
/home/Peepong/
└── mysite/
    ├── app_simple.py
    ├── final_improved_tiktok_parser_v2.py
    ├── google_parser_professional.py
    └── facebook_parser_complete.py
```

## Troubleshooting
- Make sure all parser files are uploaded
- Check that the WSGI file path is correct
- Verify packages are installed
- Check error logs in the Web tab if issues persist