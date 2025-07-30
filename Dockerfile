# Use a Python base image
FROM python:3.10-slim

# Install system dependencies, including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory inside the container
WORKDIR /app

# Install Python packages for Whisper and Translation
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install openai-whisper argostranslate

# --- UPGRADED THIS STEP ---
# Pre-download the Whisper model AND the necessary translation models
# This prevents network errors when the container runs.
RUN python -c "import whisper; whisper.load_model('base')"
# This command downloads and installs language packages for Argos Translate
# It will install packages to translate from Spanish, Japanese, French, German to English
RUN python -c "import argostranslate.package; argostranslate.package.update_package_index(); available_packages = argostranslate.package.get_available_packages(); packages_to_install = [p for p in available_packages if p.from_code in ['es', 'ja', 'fr', 'de'] and p.to_code == 'en']; [argostranslate.package.install_from_path(p.download()) for p in packages_to_install]"

# Copy our processing script into the container
COPY process_video.py .

# Set the entrypoint to run the script by default
ENTRYPOINT ["python", "process_video.py"]
```python