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
# Corrected '__name__' and ensure the url_prefix is set.
bp = Blueprint('student', __name__, url_prefix='/student')

# --- This is the complete, correct student.py file ---
# It includes all your functions like enroll_free, create_order, etc.

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

@bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        course_id = data.get('course_id')
        course = Course.query.get(course_id)
        if not course: return jsonify({'error': 'Course not found'}), 404
        if not course.price or course.price <= 0: return jsonify({'error': 'This course is not for sale.'}), 400
        order_amount = int(course.price * 100)
        razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
        order_details = {'amount': order_amount, 'currency': 'INR', 'receipt': f'order_{course_id}_{current_user.id}'}
        order = razorpay_client.order.create(order_details)
        return jsonify({
            'order_id': order['id'], 'amount': order['amount'], 'currency': order['currency'],
            'key_id': os.getenv('RAZORPAY_KEY_ID'), 'course_id': course_id, 'course_title': course.title
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Could not create payment order.'}), 500

@bp.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    data = request.json
    course_id = data.get('course_id')
    course = Course.query.get(course_id)
    if not course: return jsonify({'error': 'Course not found'}), 404
    params_dict = {
        'razorpay_order_id': data.get('razorpay_order_id'),
        'razorpay_payment_id': data.get('razorpay_payment_id'),
        'razorpay_signature': data.get('razorpay_signature')
    }
    razorpay_client = razorpay.Client(auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET')))
    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except Exception:
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
    """Translates the text portions of a VTT file using MyMemory API."""
    print(f"--- Attempting translation from '{from_lang}' to '{to_lang}' ---")
    lines = vtt_content.strip().split('\n')
    texts_to_translate = [line for line in lines if line.strip() and '-->' not in line and 'WEBVTT' not in line]
    
    if not texts_to_translate:
        print("--- No text found to translate. ---")
        return None

    try:
        separator = "|||"
        text_block = separator.join(texts_to_translate)
        api_url = f"https://api.mymemory.translated.net/get?q={text_block}&langpair={from_lang}|{to_lang}"
        
        response = requests.get(api_url, timeout=15) # Add a timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()

        if data['responseStatus'] != 200:
            print(f"--- Translation API Error: {data.get('responseDetails')} ---")
            return None

        translated_block = data['responseData']['translatedText']
        translated_list = translated_block.split(separator)

        if len(texts_to_translate) != len(translated_list):
            print("--- Translation Error: Mismatch in translated line count. ---")
            return None

        translation_map = {original: translated.strip() for original, translated in zip(texts_to_translate, translated_list)}
        
        reconstructed_lines = [translation_map.get(line, line) for line in lines]
        print("--- Translation successful! ---")
        return "\n".join(reconstructed_lines)

    except requests.exceptions.RequestException as e:
        print(f"--- Translation API call failed: {e} ---")
        return None

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
                        lang_code = metadata.get('language_code', 'en')
                        lang_name = metadata.get('language_name', 'English')
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
