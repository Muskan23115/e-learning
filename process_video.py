import sys
import os
import subprocess
import whisper
import datetime
import json
import argostranslate.package
import argostranslate.translate

def format_timestamp(seconds: float) -> str:
    """Converts seconds to VTT timestamp format HH:MM:SS.sss"""
    assert seconds >= 0, "non-negative timestamp required"
    mss = f"{(seconds - int(seconds)) * 1000:03.0f}"
    return f"{datetime.timedelta(seconds=int(seconds))}.{mss}"

def create_vtt_content(result_segments) -> str:
    """Formats a list of segments into VTT content."""
    vtt_content = "WEBVTT\n\n"
    for segment in result_segments:
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()
        vtt_content += f"{start} --> {end}\n{text}\n\n"
    return vtt_content

def translate_segments(segments, from_code, to_code="en"):
    """Translates a list of whisper segments using pre-installed models."""
    translated_segments = []
    # Load the installed translation model
    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = list(filter(lambda x: x.code == from_code, installed_languages))[0]
    to_lang = list(filter(lambda x: x.code == to_code, installed_languages))[0]
    translation = from_lang.get_translation(to_lang)

    for segment in segments:
        # Perform the translation
        translated_text = translation.translate(segment['text'])
        new_segment = segment.copy()
        new_segment['text'] = translated_text
        translated_segments.append(new_segment)
    return translated_segments

def process_video_to_subtitle(video_path: str, output_dir: str):
    """Extracts, transcribes, translates, and saves subtitles."""
    print(f"Starting processing for: {video_path}")
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    # Step 1: Extract audio
    temp_audio_path = "temp_audio.wav"
    ffmpeg_command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-y", temp_audio_path]
    print("Step 1/5: Extracting audio...")
    subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Step 2: Transcribe with Whisper
    print("Step 2/5: Transcribing audio with Whisper...")
    model = whisper.load_model("base")
    result = model.transcribe(temp_audio_path, verbose=False)
    
    video_filename = os.path.basename(video_path)
    base_filename = os.path.splitext(video_filename)[0]
    os.makedirs(output_dir, exist_ok=True)

    # Step 3: Save Original VTT
    print("Step 3/5: Saving original language .vtt file...")
    original_vtt_content = create_vtt_content(result["segments"])
    output_vtt_path = os.path.join(output_dir, f"{base_filename}.vtt")
    with open(output_vtt_path, "w", encoding="utf-8") as f:
        f.write(original_vtt_content)
    print(f"✅ Original subtitle file saved to: {output_vtt_path}")

    # Step 4: Save Language Metadata
    print("Step 4/5: Saving language metadata...")
    detected_language_code = result.get('language', 'en')
    lang_map = {'en': 'English', 'es': 'Spanish', 'ja': 'Japanese', 'fr': 'French', 'de': 'German'}
    detected_language_name = lang_map.get(detected_language_code, detected_language_code.capitalize())
    metadata = {'language_code': detected_language_code, 'language_name': detected_language_name}
    metadata_path = os.path.join(output_dir, f"{base_filename}.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved to: {metadata_path}")

    # Step 5: Translate and Save English VTT
    print("Step 5/5: Translating to English...")
    if detected_language_code != 'en':
        try:
            translated_segments = translate_segments(result["segments"], detected_language_code)
            english_vtt_content = create_vtt_content(translated_segments)
            english_vtt_path = os.path.join(output_dir, f"{base_filename}.en.vtt")
            with open(english_vtt_path, "w", encoding="utf-8") as f:
                f.write(english_vtt_content)
            print(f"✅ English subtitle file saved to: {english_vtt_path}")
        except Exception as e:
            print(f"Could not translate subtitles: {e}")
    else:
        print("Original language is English, skipping translation.")

    os.remove(temp_audio_path)
    print(f"\n✨ Processing complete for {video_filename}!")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_video.py <path_to_video> <output_directory>")
        sys.exit(1)
    process_video_to_subtitle(sys.argv[1], sys.argv[2])
