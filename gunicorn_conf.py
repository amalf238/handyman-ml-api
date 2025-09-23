# gunicorn_conf.py
import os
bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"  # Railway injects PORT
workers = 2
timeout = 120
