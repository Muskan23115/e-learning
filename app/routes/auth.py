from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Message
from app.models import User
from app import db, mail

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    # If the user is already logged in, redirect them to the correct dashboard
    if current_user.is_authenticated:
        # --- THIS IS THE FIX ---
        # We use direct URL paths here to avoid the BuildError during startup.
        if current_user.role == 'admin':
            return redirect('/admin/dashboard')
        elif current_user.role == 'teacher':
            return redirect('/teacher/dashboard')
        else:
            return redirect('/student/dashboard')
    # If not logged in, send them to the login page
    return redirect('/login')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them away from the login page
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.', 'danger')
            return redirect('/login')
            
        login_user(user, remember=request.form.get('remember'))
        
        # --- THIS IS THE FIX ---
        # The redirect logic is now here, using direct paths.
        if user.role == 'admin':
            return redirect('/admin/dashboard')
        elif user.role == 'teacher':
            return redirect('/teacher/dashboard')
        else:
            return redirect('/student/dashboard')
            
    return render_template('login.html', title='Login')

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'student')

        existing_user_email = User.query.filter_by(email=email).first()
        if existing_user_email:
            flash('Email address already exists', 'warning')
            return redirect('/signup')

        existing_user_username = User.query.filter_by(username=username).first()
        if existing_user_username:
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect('/signup')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(username=username, email=email, password=hashed_password, role=role)

        db.session.add(new_user)
        db.session.commit()

        flash('Thanks for registering! Please log in.', 'success')
        return redirect('/login')
        
    return render_template('signup.html', title='Sign Up')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

# --- PASSWORD RESET ROUTES ---

def send_reset_email(user):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps(user.email, salt='password-reset-salt')
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    # url_for is safe to use here because this function is only called after the app is running.
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@bp.route("/reset_password", methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_email(user)
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect('/login')
    return render_template('reset_password_request.html', title='Reset Password')


@bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect('/')
        
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=1800)
    except SignatureExpired:
        flash('The password reset link has expired.', 'warning')
        return redirect(url_for('auth.reset_password_request'))
    except Exception:
        flash('The password reset link is invalid.', 'warning')
        return redirect(url_for('auth.reset_password_request'))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('Invalid user.', 'warning')
        return redirect(url_for('auth.reset_password_request'))

    if request.method == 'POST':
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect('/login')
        
    return render_template('reset_password.html', title='Reset Password', token=token)
