from flask import Flask
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lms.db'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
# ==================================================

db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app) # <-- INITIALIZE MAIL

@app.template_filter('escapejs')
def escapejs_filter(text):
    return json.dumps(text)[1:-1]

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from app.routes import auth, student, teacher, admin

# Register Blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(student.bp)
app.register_blueprint(teacher.bp)
app.register_blueprint(admin.bp)
