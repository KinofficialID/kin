import os
app.secret_key = os.getenv('KEY') or os.getenv('SECRET_KEY') or 'dev-key-change-me'
ADMIN_USER = os.getenv('A_USER') or os.getenv('ADMIN_USER') or 'admin'
ADMIN_PASS = os.getenv('A_PASS') or os.getenv('ADMIN_PASSWORD') or 'admin'
