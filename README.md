E-Learning Platform (SUS LMS)
A full-featured Learning Management System (LMS) built with Python and Flask. This platform allows teachers to create and sell courses, students to enroll and learn, and administrators to manage the entire system. It includes a multi-role authentication system, payment processing, and advanced features like automatic video captioning and translation.

✨ Features
Core LMS Functionality
Multi-Role User System: Separate dashboards and permissions for Students, Teachers, and Admins.

Course Management: Teachers can create, upload, edit, and delete courses, including video content.

Student Enrollment: Students can browse available courses, purchase them, and access their enrolled courses from a personal dashboard.

Payment Processing: Secure payment integration using Razorpay for course purchases.

Admin Dashboard: Admins can view all users, manage courses, and see platform-wide statistics.

Announcements: Admins can post announcements that are visible to all users.

Advanced Video Features
Automatic Caption Generation: A powerful, Docker-based tool that uses OpenAI's Whisper model to automatically transcribe video audio into subtitle files (.vtt).

Automatic Subtitle Translation: Transcribed subtitles are automatically translated into English using a translation API, providing multi-language support.

Dynamic Subtitle Display: The video player dynamically loads both the original language and English subtitles, allowing users to switch between them.

Student & Teacher Interaction
Live Class Notifications: Teachers can schedule live classes for their courses. When a class is scheduled, an email notification is automatically sent to every student enrolled in that course with the class details and meeting link.

Password Reset: Secure "Forgot Password" functionality that sends a time-sensitive reset link to the user's email.

🛠️ Technology Stack
Backend: Python, Flask

Database: SQLite with SQLAlchemy and Flask-Migrate

Authentication: Flask-Login

Frontend: HTML, CSS, JavaScript

Payment Gateway: Razorpay

Video Processing:

FFmpeg: For audio extraction.

OpenAI Whisper: For speech-to-text transcription.

Containerization: Docker

Email: Flask-Mail

🚀 Setup and Installation
Follow these steps to get the project running locally.

Prerequisites
Python 3.10+

Docker Desktop

A virtual environment tool (like venv)

1. Clone the Repository
git clone <your-repository-url>
cd e-learning

2. Set Up the Python Environment
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install required Python packages
pip install -r requirements.txt
pip install Flask-Migrate requests

3. Configure Environment Variables
Create a .env file in the root directory and add your configuration details.

SECRET_KEY='a_very_secret_key'
DATABASE_URL='sqlite:///lms.db'

# Your Gmail App Password (if using Gmail)
EMAIL_USER='your_email@gmail.com'
EMAIL_PASS='your_app_password'

# Razorpay API Keys
RAZORPAY_KEY_ID='your_razorpay_key_id'
RAZORPAY_KEY_SECRET='your_razorpay_key_secret'

4. Set Up the Database
# Initialize the database migrations folder (only needs to be done once)
flask db init

# Generate the initial migration script
flask db migrate -m "Initial database setup"

# Apply the migration to create the database
flask db upgrade

▶️ Running the Project
1. Start the Web Server
python run.py

The application will be running at http://127.0.0.1:5000.

2. Build the Captioning Tool
This is a one-time setup for the video processing tool.

docker build -t e-learning-processor .

📝 Usage: Generating Subtitles for a New Video
To generate captions for a new video you've added to the app/static/uploads/ folder:

Open a new terminal in the project root directory.

Run the Docker command, replacing your_video_name.mp4 with the name of your file.

docker run --rm -v "$(pwd):/app" e-learning-processor app/static/uploads/your_video_name.mp4 app/static/subtitles

This will automatically create the original language .vtt file and the language metadata .json file in the app/static/subtitles/ directory. The next time a student views that course, the English translation will be generated automatically.