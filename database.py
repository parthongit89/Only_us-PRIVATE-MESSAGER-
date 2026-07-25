import logging
import psycopg2
from urllib.parse import urlparse
from extensions import db
from models import User, AccountRequest, Conversation, ConversationMember, Message, Notification
from config import Config

logger = logging.getLogger(__name__)

def ensure_postgres_db(pg_url):
    """Checks if PostgreSQL database exists, and creates it if missing."""
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
        if ensure_postgres_db(pg_url):
            try:
                # Test connection
                url = urlparse(pg_url)
                conn = psycopg2.connect(
                    dbname=url.path.lstrip('/'),
                    user=url.username,
                    password=url.password,
                    host=url.hostname or 'localhost',
                    port=url.port or 5432
                )
                conn.close()
                print("Using PostgreSQL database.")
                return
            except Exception as e:
                print(f"PostgreSQL connection failed: {e}")

    print("Falling back to SQLite database.")
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLITE_FALLBACK_URL

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

    # Seed Admin Account if missing
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='AdminUser',
            email='admin@onlyus.app',
            passcode='1234',
            role='admin',
            status='approved',
            bio='System Administrator',
            avatar='default_avatar.png'
        )
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()

    # Seed sample approved users for chat testing if empty
    user_count = User.query.count()
    if user_count <= 2:
        u1 = User(username='Alex Rivers', email='alex@onlyus.app', passcode='1234', role='user', status='approved', bio='Tech enthusiast', is_online=True)
        u1.set_password('UserPass123!')
        
        u2 = User(username='Sarah Connor', email='sarah@onlyus.app', passcode='1234', role='user', status='approved', bio='Design lead', is_online=True)
        u2.set_password('UserPass123!')

        u3 = User(username='Michael Scott', email='michael@onlyus.app', passcode='1234', role='user', status='approved', bio='Regional Manager', is_online=False)
        u3.set_password('UserPass123!')

        db.session.add_all([u1, u2, u3])
        db.session.commit()

        # Seed sample pending account requests matching admin.png design with 4-digit passcodes
        req1 = AccountRequest(email='exampleuser@gmail.com', passcode='9823', status='pending', note='Request application for creating Account')
        req2 = AccountRequest(email='exampleuser2@gmail.com', passcode='4710', from_email='exampleuser@gmail.com', for_email='exampleuser2@gmail.com', status='pending', note='Request application for creating Account')
        req3 = AccountRequest(email='exampleuser3@gmail.com', passcode='3154', status='pending', note='Request application for creating Account')
        req4 = AccountRequest(email='exampleuser4@gmail.com', passcode='8092', from_email='exampleuser3@gmail.com', for_email='exampleuser4@gmail.com', status='pending', note='Request application for creating Account')
        
        db.session.add_all([req1, req2, req3, req4])
        db.session.commit()

        # Seed sample initial conversation between owner and Alex Rivers
        conv = Conversation(is_group=False)
        db.session.add(conv)
        db.session.commit()

        cm1 = ConversationMember(conversation_id=conv.id, user_id=owner.id)
        cm2 = ConversationMember(conversation_id=conv.id, user_id=u1.id)
        db.session.add_all([cm1, cm2])

        msg1 = Message(conversation_id=conv.id, sender_id=u1.id, content='Hey there! Welcome to OnlyUs.', status='read')
        msg2 = Message(conversation_id=conv.id, sender_id=owner.id, content='Thanks! Private and secure messaging looks great in dark mode.', status='read')
        db.session.add_all([msg1, msg2])
        db.session.commit()

        # Seed sample notifications
        notif1 = Notification(user_id=owner.id, title='Welcome to OnlyUs', message='Your secure private space is ready.', type='system')
        notif2 = Notification(user_id=owner.id, title='New Account Request', message='exampleuser@gmail.com requested access.', type='request')
        db.session.add_all([notif1, notif2])
        db.session.commit()
