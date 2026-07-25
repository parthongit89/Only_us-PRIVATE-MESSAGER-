import os
from flask import Flask
from config import Config
from extensions import db, login_manager, migrate, socketio
from database import verify_and_select_database, init_db
from blueprints.auth.routes import auth_bp
from blueprints.chat.routes import chat_bp
from blueprints.admin.routes import admin_bp
from blueprints.user.routes import user_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Verify PostgreSQL or select SQLite fallback before init_app
    verify_and_select_database(app)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    # Initialize and seed database
    init_db(app)

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting OnlyUs Application on port {port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
