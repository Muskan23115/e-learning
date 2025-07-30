
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import os
import json

# Create extension instances without attaching them to an app yet
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app():
    """
    An application factory to structure the Flask app correctly.
    """
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///lms.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
    app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
    app.config['MAIL_DEBUG'] = True

    # --- Initialize Extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db) # Initialize Migrate here

    # --- Login Manager Setup ---
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        # Import here to avoid circular import errors
        from .models import User
        return User.query.get(int(user_id))

    # --- Register Blueprints ---
    # Use a context to ensure the app is ready before importing routes
    with app.app_context():
        from .routes import auth, student, teacher, admin

        app.register_blueprint(auth.bp)
        app.register_blueprint(student.bp)
        app.register_blueprint(teacher.bp)
        app.register_blueprint(admin.bp)

    return app

