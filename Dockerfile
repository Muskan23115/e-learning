# Use a Python base image
FROM python:3.10-slim

# Install system dependencies, including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /app

# Install Python packages for Whisper
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install openai-whisper

# --- ADDED THIS STEP ---
# Pre-download the Whisper model during the build process
# This prevents network errors when the container runs.
RUN python -c "import whisper; whisper.load_model('base')"

# Copy our processing script into the container
COPY process_video.py .

# Set the entrypoint to run the script by default
ENTRYPOINT ["python", "process_video.py"]
