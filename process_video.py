import sys
import os
import subprocess
import whisper
import datetime

def format_timestamp(seconds: float) -> str:
    """Converts seconds to VTT timestamp format HH:MM:SS.sss"""
    assert seconds >= 0, "non-negative timestamp required"
    mss = f"{(seconds - int(seconds)) * 1000:03.0f}"
    return f"{datetime.timedelta(seconds=int(seconds))}.{mss}"

def create_vtt_content(result: dict) -> str:
    """Formats the Whisper transcription result into VTT content."""
    vtt_content = "WEBVTT\n\n"
    for segment in result["segments"]:
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()
        vtt_content += f"{start} --> {end}\n{text}\n\n"
    return vtt_content

def process_video_to_subtitle(video_path: str, output_dir: str):
    """Extracts audio, transcribes it, and saves it as a .vtt file."""
    print(f"Starting processing for: {video_path}")
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    # 1. Extract audio using FFmpeg to a temporary file
    temp_audio_path = "temp_audio.wav"
    ffmpeg_command = [
        "ffmpeg", "-i", video_path, "-vn",
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        "-y", temp_audio_path
    ]
    print("Step 1/3: Extracting audio...")
    subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 2. Transcribe audio using Whisper
    print("Step 2/3: Transcribing audio with Whisper...")
    model = whisper.load_model("base") # "base" model is a good starting point
    result = model.transcribe(temp_audio_path, verbose=False)

    # 3. Format as VTT and save to the specified directory
    print("Step 3/3: Saving .vtt subtitle file...")
    vtt_content = create_vtt_content(result)
    
    video_filename = os.path.basename(video_path)
    base_filename = os.path.splitext(video_filename)[0]
    output_vtt_path = os.path.join(output_dir, f"{base_filename}.vtt")

    with open(output_vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)
    
    # Clean up the temporary audio file
    os.remove(temp_audio_path)
    print(f"✅ Success! Subtitle file saved to: {output_vtt_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_video.py <path_to_video> <output_directory>")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_folder = sys.argv[2]
    process_video_to_subtitle(input_video, output_folder)