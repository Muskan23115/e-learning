from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import Course, Purchase, Announcement, AnnouncementRead
from app import db
import os
from werkzeug.utils import secure_filename
from collections import Counter

bp = Blueprint('teacher', __name__)

@bp.route('/teacher/announcement_read/<int:announcement_id>', methods=['POST'])
@login_required
def announcement_read(announcement_id):
    if not AnnouncementRead.query.filter_by(user_id=current_user.id, announcement_id=announcement_id).first():
        ar = AnnouncementRead(user_id=current_user.id, announcement_id=announcement_id)
        db.session.add(ar)
        db.session.commit()
    return ('', 204)

@bp.route('/teacher/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = float(request.form['price'])
        video_file = request.files.get('video')
        
        video_url = None
        
        # Save video if it exists
        if video_file and video_file.filename:
            video_filename = secure_filename(video_file.filename)
            video_path = os.path.join(current_app.root_path, 'static', 'uploads', video_filename)
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            video_file.save(video_path)
            # Store the path that the web server can use
            video_url = f'static/uploads/{video_filename}'

        # Create the course object without the old fields
        new_course = Course(
            title=title,
            description=description,
            teacher_id=current_user.id,
            price=price,
            video_url=video_url
        )
        db.session.add(new_course)
        db.session.commit()
        flash('Course uploaded successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))

    # --- This GET request logic remains the same ---
    my_courses = Course.query.filter_by(teacher_id=current_user.id).all()
    purchases = Purchase.query.join(Course).filter(Course.teacher_id == current_user.id).all()
    total_earnings = sum(p.amount for p in purchases)
    total_courses = len(my_courses)
    student_ids = set(p.student_id for p in purchases)
    total_students = len(student_ids)
    
    best_course = None
    if purchases:
        course_counts = Counter([p.course_id for p in purchases])
        best_course_id = course_counts.most_common(1)[0][0]
        best_course = Course.query.get(best_course_id)
        
    all_announcements = Announcement.query.order_by(Announcement.timestamp.desc()).all()
    read_ids = {ar.announcement_id for ar in AnnouncementRead.query.filter_by(user_id=current_user.id).all()}
    unread_announcements = [a for a in all_announcements if a.id not in read_ids]
    
    return render_template(
        'dashboard_teacher.html',
        my_courses=my_courses,
        total_earnings=total_earnings,
        total_courses=total_courses,
        total_students=total_students,
        best_course=best_course,
        unread_announcements=unread_announcements
    )

@bp.route('/teacher/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        flash('You are not authorized to edit this course.', 'danger')
        return redirect(url_for('teacher.dashboard'))
        
    if request.method == 'POST':
        course.title = request.form['title']
        course.description = request.form['description']
        course.price = float(request.form['price'])
        video_file = request.files.get('video')
        
        # Update video if a new one is uploaded
        if video_file and video_file.filename:
            video_filename = secure_filename(video_file.filename)
            video_path = os.path.join(current_app.root_path, 'static', 'uploads', video_filename)
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            video_file.save(video_path)
            course.video_url = f'static/uploads/{video_filename}'
            
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('teacher.dashboard'))
        
    return render_template('teacher_edit_course.html', course=course)

@bp.route('/teacher/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        flash('You are not authorized to delete this course.', 'danger')
        return redirect(url_for('teacher.dashboard'))
        
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('teacher.dashboard'))
