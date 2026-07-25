import logging
try:
    import psycopg2
except Exception:
    psycopg2 = None
from urllib.parse import urlparse
from sqlalchemy import create_engine
from extensions import db
from models import User, AccountRequest, Conversation, ConversationMember, Message, Notification
from config import Config

logger = logging.getLogger(__name__)

def ensure_postgres_db(pg_url):
    """Checks if PostgreSQL database exists, and creates it if missing."""
    if not psycopg2:
        return False
    try:
        url = urlparse(pg_url)
        dbname = url.path.lstrip('/')
        user = url.username
        password = url.password
        host = url.hostname or 'localhost'
        port = url.port or 5432

        conn = psycopg2.connect(
            dbname='postgres',
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (dbname,))
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f'CREATE DATABASE "{dbname}";')
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.warning(f"Could not auto-create PostgreSQL database: {e}")
        return False

def verify_and_select_database(app):
    """Verifies PostgreSQL connectivity or falls back to SQLite before db.init_app."""
    pg_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    if pg_url and 'postgresql' in pg_url:
        for attempt in range(3):
            try:
                engine = create_engine(pg_url, pool_pre_ping=True)
                with engine.connect() as conn:
                    logger.info("Successfully connected to PostgreSQL database.")
                engine.dispose()
                return True
            except Exception as e:
                logger.warning(f"PostgreSQL connection attempt {attempt+1} failed: {e}")
                import time
                time.sleep(1)

        # If PostgreSQL connection fails, fallback to SQLite
        logger.warning("Falling back to SQLite database.")
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('SQLITE_FALLBACK_URL')

def init_db(app):
    with app.app_context():
        db.create_all()
        seed_initial_data()

def seed_initial_data():
    # Seed Owner Account if missing
    owner = User.query.filter_by(role='owner').first()
    if not owner:
        owner = User(
            username='Owner',
            email='owner@onlyus.app',
            passcode='1234',
            role='owner',
            status='approved',
            bio='System Owner',
            avatar='default_avatar.png'
        )
        owner.set_password('OwnerPass123!')
        db.session.add(owner)
        db.session.commit()

    # Seed Admin Account
    admin = User.query.filter_by(email='sonavaneparth388@gmail.com').first() or User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='Sonavaneparth388',
            email='sonavaneparth388@gmail.com',
            passcode='2325',
            role='admin',
            status='approved',
            bio='System Administrator',
            avatar='default_avatar.png'
        )
        admin.set_password('admin223')
        db.session.add(admin)
        db.session.commit()
    else:
        admin.username = 'Sonavaneparth388'
        admin.email = 'sonavaneparth388@gmail.com'
        admin.passcode = '2325'
        admin.role = 'admin'
        admin.status = 'approved'
        admin.set_password('admin223')
        db.session.commit()
