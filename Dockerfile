# Use a Python base image
FROM python:3.10-slim

# Install system dependencies, including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /app

# Install Python packages for Whisper
# Note: Using a specific torch version compatible with CPU-only can speed up build
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install openai-whisper

# Copy our processing script into the container
COPY process_video.py .

# Set the entrypoint to run the script by default
ENTRYPOINT ["python", "process_video.py"]