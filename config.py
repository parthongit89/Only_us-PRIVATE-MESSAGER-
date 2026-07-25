import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'onlyus_super_secret_key_2026_privacy_first')
    
    # Primary PostgreSQL Database URL matching pgAdmin database name 'onlyus'
    PG_DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:parthpostgress89%23%23@localhost:5432/onlyus')
    SQLITE_FALLBACK_URL = os.environ.get('FALLBACK_SQLITE_URL', 'sqlite:///onlyus.db')
    
    SQLALCHEMY_DATABASE_URI = PG_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Mail Config
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
