# FinBridge - Recruitment Platform

A full-stack Flask website where:
- CA students can register, build profile, and apply to jobs.
- Companies can register, update profile, post jobs, and manage applications.
- Admin can manage users and jobs in one panel.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

## Default admin

- Email: `admin@cabridge.com`
- Password: `admin123`

You can override via environment variables:
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `SECRET_KEY`
- `DATABASE_URL`
