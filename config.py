import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'onlyus_super_secret_key_2026_privacy_first')
    
    # Session & Remember Me Configuration (90 Days Lifetime)
    PERMANENT_SESSION_LIFETIME = timedelta(days=90)
    REMEMBER_COOKIE_DURATION = timedelta(days=90)
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


    
    raw_pg_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:parthpostgress89%23%23@localhost:5432/onlyus')
    if raw_pg_url and raw_pg_url.startswith("postgres://"):
        raw_pg_url = raw_pg_url.replace("postgres://", "postgresql://", 1)

    PG_DATABASE_URL = raw_pg_url
    SQLITE_FALLBACK_URL = os.environ.get('FALLBACK_SQLITE_URL', 'sqlite:///onlyus.db')
    
    SQLALCHEMY_DATABASE_URI = PG_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30
    }
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Mail Config
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
