from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Course, Purchase, Transaction, Announcement, AnnouncementRead
from app import db
import razorpay
import os
import time
import traceback
import json
import requests # For making API calls
import re # For parsing VTT files

bp = Blueprint('student', __name__)

# ... (all your other routes like enroll_free, create_order, etc. remain here) ...

def translate_vtt_content(vtt_content, from_lang, to_lang='en'):
    """Translates the text portions of a VTT file using MyMemory API."""
    lines = vtt_content.strip().split('\n')
    translated_lines = []
    
    # Regex to find text lines (that don't have '-->' and are not timestamps)
    text_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{3}\s-->\s\d{2}:\d{2}:\d{2}\.\d{3}$')
    
    # Collect all text to translate in one batch
    texts_to_translate = []
    for line in lines:
        if line.strip() and not text_pattern.match(line) and 'WEBVTT' not in line:
            texts_to_translate.append(line)
            
    # API call to translate the batch
    translated_texts = {}
    if texts_to_translate:
        try:
            # Join with a unique separator to translate as one block
            separator = "|||"
            text_block = separator.join(texts_to_translate)
            api_url = f"https://api.mymemory.translated.net/get?q={text_block}&langpair={from_lang}|{to_lang}"
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            translated_block = data['responseData']['translatedText']
            
            # Split the translated block back into individual lines
            translated_list = translated_block.split(separator)
            
            # Create a mapping from original text to translated text
            if len(texts_to_translate) == len(translated_list):
                 for i in range(len(texts_to_translate)):
                    translated_texts[texts_to_translate[i]] = translated_list[i].strip()

        except requests.exceptions.RequestException as e:
            print(f"Translation API call failed: {e}")
            return None # Return None if translation fails

    # Reconstruct the VTT file with translated text
    for line in lines:
        if line in translated_texts:
            translated_lines.append(translated_texts[line])
        else:
            translated_lines.append(line)
            
    return "\n".join(translated_lines)


@bp.route('/student/course/<int:course_id>')
@login_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    purchased = any(p.course_id == course_id for p in current_user.purchases)
    if not purchased:
        flash('You have not purchased this course.', 'danger')
        return redirect(url_for('student.dashboard'))

    subtitle_file = None
    english_subtitle_file = None
    lang_code = 'en'
    lang_name = 'English'

    if course.video_url:
        video_filename_only = os.path.basename(course.video_url)
        base_filename = video_filename_only.rsplit('.', 1)[0]
        
        original_vtt_filename = f"{base_filename}.vtt"
        original_vtt_path = os.path.join(current_app.root_path, 'static', 'subtitles', original_vtt_filename)
        
        if os.path.exists(original_vtt_path):
            subtitle_file = original_vtt_filename

            # Read language metadata
            metadata_filename = f"{base_filename}.json"
            metadata_path = os.path.join(current_app.root_path, 'static', 'subtitles', metadata_filename)
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        lang_code = metadata.get('language_code', lang_code)
                        lang_name = metadata.get('language_name', lang_name)
                except (IOError, json.JSONDecodeError):
                    pass
            
            # --- NEW LOGIC: TRANSLATE ON-THE-FLY ---
            english_vtt_filename = f"{base_filename}.en.vtt"
            english_vtt_path = os.path.join(current_app.root_path, 'static', 'subtitles', english_vtt_filename)
            
            # Only translate if the English file doesn't exist and the original language isn't English
            if not os.path.exists(english_vtt_path) and lang_code != 'en':
                print(f"Translating {original_vtt_filename} to English...")
                with open(original_vtt_path, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                
                translated_content = translate_vtt_content(vtt_content, lang_code)
                
                if translated_content:
                    with open(english_vtt_path, 'w', encoding='utf-8') as f:
                        f.write(translated_content)
                    print("Translation saved.")
            
            if os.path.exists(english_vtt_path):
                english_subtitle_file = english_vtt_filename
            # ----------------------------------------

    return render_template(
        'student_view_course.html', 
        course=course, 
        subtitle_file=subtitle_file,
        english_subtitle_file=english_subtitle_file,
        lang_code=lang_code,
        lang_name=lang_name
    )