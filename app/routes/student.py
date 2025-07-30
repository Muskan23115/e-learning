from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Course, Purchase, Transaction, Announcement, AnnouncementRead
from app import db
import razorpay
import os
import time
import traceback
import json
import requests
import re

# --- THIS IS THE FIX ---
# We are telling Flask that every URL in this file should start with '/student'
bp = Blueprint('student', __name__, url_prefix='/student')

# ==============================================================================
# RESTORED ROUTE: For enrolling in free courses
# ==============================================================================
@bp.route('/enroll_free', methods=['POST'])
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

# --- Other necessary routes are also restored below ---

@bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    # This function's content is restored from your original code
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
        razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
        order = razorpay_client.order.create(order_details)
        return jsonify({
            'order_id': order['id'], 'amount': order['amount'], 'currency': order['currency'],
            'key_id': os.getenv('RAZORPAY_KEY_ID'), 'course_id': course_id, 'course_title': course.title
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'An internal error occurred.'}), 500

@bp.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    # This function's content is restored from your original code
    data = request.json
    course_id = data.get('course_id')
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')
    course = Course.query.get(course_id)
    if not course:
        return jsonify({'error': 'Course not found'}), 404
    params_dict = {'razorpay_order_id': order_id, 'razorpay_payment_id': payment_id, 'razorpay_signature': signature}
    razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
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

@bp.route('/announcement_read/<int:announcement_id>', methods=['POST'])
@login_required
def announcement_read(announcement_id):
    # This function's content is restored from your original code
    if not AnnouncementRead.query.filter_by(user_id=current_user.id, announcement_id=announcement_id).first():
        ar = AnnouncementRead(user_id=current_user.id, announcement_id=announcement_id)
        db.session.add(ar)
        db.session.commit()
    return ('', 204)

@bp.route('/dashboard')
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

def translate_vtt_content(vtt_content, from_lang, to_lang='en'):
    lines = vtt_content.strip().split('\n')
    translated_lines = []
    text_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s-->\s\d{2}:\d{2}:\d{2}\.\d{3}$')
    texts_to_translate = [line for line in lines if line.strip() and not text_pattern.match(line) and 'WEBVTT' not in line]
    translated_texts = {}
    if texts_to_translate:
        try:
            separator = "|||"
            text_block = separator.join(texts_to_translate)
            api_url = f"https://api.mymemory.translated.net/get?q={text_block}&langpair={from_lang}|{to_lang}"
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            translated_block = data['responseData']['translatedText']
            translated_list = translated_block.split(separator)
            if len(texts_to_translate) == len(translated_list):
                for i in range(len(texts_to_translate)):
                    translated_texts[texts_to_translate[i]] = translated_list[i].strip()
        except requests.exceptions.RequestException as e:
            print(f"Translation API call failed: {e}")
            return None
    for line in lines:
        translated_lines.append(translated_texts.get(line, line))
    return "\n".join(translated_lines)

@bp.route('/course/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    purchased = any(p.course_id == course_id for p in current_user.purchases)
    if not purchased:
        flash('You have not purchased this course.', 'danger')
        return redirect(url_for('student.dashboard'))

    subtitle_file, english_subtitle_file, lang_code, lang_name = None, None, 'en', 'English'
    if course.video_url:
        video_filename_only = os.path.basename(course.video_url)
        base_filename = video_filename_only.rsplit('.', 1)[0]
        original_vtt_filename = f"{base_filename}.vtt"
        original_vtt_path = os.path.join(current_app.root_path, 'static', 'subtitles', original_vtt_filename)
        if os.path.exists(original_vtt_path):
            subtitle_file = original_vtt_filename
            metadata_filename = f"{base_filename}.json"
            metadata_path = os.path.join(current_app.root_path, 'static', 'subtitles', metadata_filename)
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        lang_code = metadata.get('language_code', lang_code)
                        lang_name = metadata.get('language_name', lang_name)
                except (IOError, json.JSONDecodeError): pass
            
            english_vtt_filename = f"{base_filename}.en.vtt"
            english_vtt_path = os.path.join(current_app.root_path, 'static', 'subtitles', english_vtt_filename)
            if not os.path.exists(english_vtt_path) and lang_code != 'en':
                with open(original_vtt_path, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                translated_content = translate_vtt_content(vtt_content, lang_code)
                if translated_content:
                    with open(english_vtt_path, 'w', encoding='utf-8') as f:
                        f.write(translated_content)
            if os.path.exists(english_vtt_path):
                english_subtitle_file = english_vtt_filename
    return render_template(
        'student_view_course.html', 
        course=course, subtitle_file=subtitle_file,
        english_subtitle_file=english_subtitle_file,
        lang_code=lang_code, lang_name=lang_name
    )
