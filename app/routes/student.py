from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Course, Purchase, Transaction, Announcement, AnnouncementRead
from app import db
import razorpay
import os
import time
import traceback
import json # Import the json library

bp = Blueprint('student', __name__)

razorpay_client = razorpay.Client(
    auth=(
        os.getenv('RAZORPAY_KEY_ID', 'rzp_test_1DP5mmOlF5G5ag'),
        os.getenv('RAZORPAY_KEY_SECRET', '0TrjAPO9uUnJ9d2hElVkyv0i')
    )
)


@bp.route('/student/enroll_free', methods=['POST'])
@login_required
def enroll_free():
    try:
        course_id = request.form.get('course_id')
        course = Course.query.get(course_id)

        if not course:
            flash('Course not found.', 'danger')
            return redirect(url_for('student.dashboard'))
        
        if course.price and course.price > 0:
            flash('This course is not free.', 'danger')
            return redirect(url_for('student.dashboard'))

        is_already_purchased = Purchase.query.filter_by(student_id=current_user.id, course_id=course.id).first()
        if is_already_purchased:
            flash('You are already enrolled in this course.', 'info')
            return redirect(url_for('student.dashboard'))

        purchase = Purchase(student_id=current_user.id, course_id=course.id, amount=0)
        db.session.add(purchase)
        db.session.commit()
        
        flash(f'You have successfully enrolled in {course.title}!', 'success')

    except Exception as e:
        traceback.print_exc()
        flash('An error occurred while enrolling.', 'danger')

    return redirect(url_for('student.dashboard'))


@bp.route('/student/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        course = Course.query.get(course_id)

        if not course:
            return jsonify({'error': 'Course not found'}), 404

        if not course.price or course.price <= 0:
            return jsonify({'error': 'This course cannot be purchased. It might be free.'}), 400

        order_amount = int(course.price * 100)
        order_currency = 'INR'
        order_receipt = f'order_rcptid_{course_id}_{current_user.id}_{int(time.time())}'
        
        order_details = {'amount': order_amount, 'currency': order_currency, 'receipt': order_receipt}
        order = razorpay_client.order.create(order_details)

        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': os.getenv('RAZORPAY_KEY_ID', 'rzp_test_1DP5mmOlF5G5ag'),
            'course_id': course_id,
            'course_title': course.title
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'An internal error occurred. Could not create payment order.'}), 500


@bp.route('/student/payment_success', methods=['POST'])
@login_required
def payment_success():
    data = request.json
    course_id = data.get('course_id')
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404

    params_dict = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }
    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except Exception as e:
        return jsonify({'error': 'Payment verification failed'}), 400

    purchase = Purchase(student_id=current_user.id, course_id=course.id, amount=course.price)
    db.session.add(purchase)
    db.session.commit()
    teacher_amount = course.price * 0.9
    admin_amount = course.price * 0.1
    transaction = Transaction(purchase_id=purchase.id, teacher_amount=teacher_amount, admin_amount=admin_amount, status='paid')
    db.session.add(transaction)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/student/announcement_read/<int:announcement_id>', methods=['POST'])
@login_required
def announcement_read(announcement_id):
    if not AnnouncementRead.query.filter_by(user_id=current_user.id, announcement_id=announcement_id).first():
        ar = AnnouncementRead(user_id=current_user.id, announcement_id=announcement_id)
        db.session.add(ar)
        db.session.commit()
    return ('', 204)

@bp.route('/student/dashboard')
@login_required
def dashboard():
    purchased_ids = [p.course_id for p in current_user.purchases]
    available_courses = Course.query.filter(~Course.id.in_(purchased_ids)).all()
    purchased_courses = [p.course for p in current_user.purchases]
    order_history = current_user.purchases
    
    all_announcements = Announcement.query.order_by(Announcement.timestamp.desc()).all()
    read_ids = {ar.announcement_id for ar in AnnouncementRead.query.filter_by(user_id=current_user.id).all()}
    unread_announcements = [a for a in all_announcements if a.id not in read_ids]
    
    return render_template(
        'dashboard_student.html',
        available_courses=available_courses,
        purchased_courses=purchased_courses,
        order_history=order_history,
        unread_announcements=unread_announcements
    )

@bp.route('/student/course/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    purchased = any(p.course_id == course_id for p in current_user.purchases)
    if not purchased:
        flash('You have not purchased this course.', 'danger')
        return redirect(url_for('student.dashboard'))

    subtitle_file = None
    lang_code = 'en'
    lang_name = 'English'

    if course.video_url:
        video_filename_only = os.path.basename(course.video_url)
        base_filename = video_filename_only.rsplit('.', 1)[0]
        subtitle_file = f"{base_filename}.vtt"

        # --- NEW LOGIC: READ LANGUAGE METADATA ---
        metadata_filename = f"{base_filename}.json"
        metadata_path = os.path.join(current_app.root_path, 'static', 'subtitles', metadata_filename)
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    lang_code = metadata.get('language_code', lang_code)
                    lang_name = metadata.get('language_name', lang_name)
            except (IOError, json.JSONDecodeError):
                pass # Use default values if file is broken
        # -----------------------------------------

    return render_template(
        'student_view_course.html', 
        course=course, 
        subtitle_file=subtitle_file,
        lang_code=lang_code,
        lang_name=lang_name
    )