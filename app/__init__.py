
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os
import json

# Create extension instances without attaching them to an app yet
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    """
    An application factory, which is the standard way to create Flask apps.
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

    # --- Login Manager Setup ---
    login_manager.login_view = 'auth.login' # The page to redirect to for login

    @login_manager.user_loader
    def load_user(user_id):
        # We need to import User here to avoid circular imports
        from .models import User
        return User.query.get(int(user_id))

    # --- Register Blueprints ---
    with app.app_context():
        from .routes import auth, student, teacher, admin

        app.register_blueprint(auth.bp)
        app.register_blueprint(student.bp)
        app.register_blueprint(teacher.bp)
        app.register_blueprint(admin.bp)

    return app