# Smart Uni Sidekick LMS

A Barbie-core inspired, full-featured Learning Management System built with Flask.

## Features
- Student, Teacher, and Admin dashboards
- Course upload (video, notes), purchase, and access
- Razorpay payment integration (90/10 split)
- Modern, glassmorphic, pastel UI

## Setup
1. **Clone the repo**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set environment variables:**
   - `SECRET_KEY` (Flask secret)
   - `RAZORPAY_KEY_ID` (your Razorpay key)
   - `RAZORPAY_KEY_SECRET` (your Razorpay secret)
4. **Initialize the database:**
   ```bash
   python
   >>> from app import db
   >>> db.create_all()
   >>> exit()
   ```
5. **Run locally:**
   ```bash
   python run.py
   ```

## Deployment (Heroku/Render/Other)
- Use the provided `Procfile` and `wsgi.py`
- Make sure to set environment variables in your deployment dashboard
- Static files and uploads are served from `/app/static/`

## Notes
- For production, use a real database (Postgres, MySQL, etc.)
- Add your own branding and features as needed! 