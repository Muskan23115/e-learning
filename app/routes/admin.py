from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import User, Course, Transaction, SupportMessage, Announcement
from collections import defaultdict
from collections import Counter
from app import db

bp = Blueprint('admin', __name__)

@bp.route('/admin/dashboard')
@login_required
def dashboard():
    users = User.query.all()
    courses = Course.query.all()
    transactions = Transaction.query.all()
    platform_earnings = sum(t.admin_amount for t in transactions)
    total_users = len(users)
    total_courses = len(courses)
    total_transactions = len(transactions)
    # Top-earning teacher
    teacher_earnings = defaultdict(float)
    for t in transactions:
        if t.purchase and t.purchase.course:
            teacher_earnings[t.purchase.course.teacher_id] += t.teacher_amount
    top_teacher = None
    if teacher_earnings:
        top_teacher_id = max(teacher_earnings, key=teacher_earnings.get)
        top_teacher = User.query.get(top_teacher_id)
    # Most popular course
    course_counts = Counter([t.purchase.course_id for t in transactions if t.purchase and t.purchase.course_id])
    popular_course = None
    if course_counts:
        popular_course_id = course_counts.most_common(1)[0][0]
        popular_course = Course.query.get(popular_course_id)
    return render_template(
        'dashboard_admin.html',
        users=users,
        courses=courses,
        transactions=transactions,
        platform_earnings=platform_earnings,
        total_users=total_users,
        total_courses=total_courses,
        total_transactions=total_transactions,
        top_teacher=top_teacher,
        popular_course=popular_course
    )

@bp.route('/admin/support')
@login_required
def support():
    messages = SupportMessage.query.order_by(SupportMessage.timestamp.desc()).all()
    return render_template('admin_support.html', messages=messages)

@bp.route('/admin/announcements', methods=['GET', 'POST'])
@login_required
def announcements():
    if request.method == 'POST':
        message = request.form['message']
        if message.strip():
            a = Announcement(message=message)
            db.session.add(a)
            db.session.commit()
            flash('Announcement posted!', 'success')
        return redirect(url_for('admin.announcements'))
    all_announcements = Announcement.query.order_by(Announcement.timestamp.desc()).all()
    return render_template('admin_announcements.html', announcements=all_announcements)

# Add admin dashboard routes here 