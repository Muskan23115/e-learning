from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, SupportMessage
from app import db, mail # <-- ADDED: Import 'mail'
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message # <-- ADDED: For sending emails

bp = Blueprint('auth', __name__)

# ==================================================
# HELPER FUNCTION TO SEND THE RESET EMAIL
# ==================================================
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com', # Can be a generic sender
                  recipients=[user.email])
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg.html = render_template('email/reset_email.html', reset_url=reset_url)
    mail.send(msg)

# ==================================================
# NEW ROUTES FOR PASSWORD RESET LOGIC
# ==================================================
@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_email(user)
        # Flash message regardless of whether user exists to prevent email enumeration
        flash('If an account with that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_password_request.html')

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired token.', 'danger')
        return redirect(url_for('auth.reset_password_request'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        if password != password2:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        hashed_password = generate_password_hash(password)
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_password.html', token=token)

# ==================================================
# EXISTING ROUTES BELOW
# ==================================================

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'student':
                return redirect(url_for('student.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.', 'danger')
            return redirect(url_for('auth.login'))
        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@bp.route('/contact', methods=['POST'])
def contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    support = SupportMessage(name=name, email=email, message=message)
    db.session.add(support)
    db.session.commit()
    flash('Your message has been sent! We will get back to you soon.', 'success')
    return redirect(url_for('auth.index'))

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
