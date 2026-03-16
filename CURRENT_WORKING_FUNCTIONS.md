# Campus Bridge Website - Current Working Functions

This document lists the functions that are currently implemented and working in the Flask website.

## Core Setup

- Flask app with SQLAlchemy and Flask-Login.
- SQLite database by default: `instance/campus_bridge.db`.
- Default admin auto-created at startup if missing:
  - Email: `admin@cabridge.com`
  - Password: `admin123`

## Data Models

- `User`
  - Roles: `student`, `company`, `admin`
  - Active/inactive account support
- `StudentProfile`
  - One-to-one with student user
- `CompanyProfile`
  - One-to-one with company user
- `Job`
  - Created by company users
  - Can be active/inactive
- `Application`
  - Student applies to a job
  - Unique per `(job_id, student_id)`
  - Status: `pending`, `shortlisted`, `rejected`, `selected`

## Auth and Access Control

- `role_required(*roles)` decorator protects routes by role.
- Inactive users cannot log in.
- Login redirects by role:
  - Student -> student dashboard
  - Company -> company dashboard
  - Admin -> admin dashboard

## Public Pages and Functions

- `GET /`
  - Home page with active jobs list.
- `GET /about`
  - About page.
- `GET/POST /contact`
  - Validates required fields (`name`, `email`, `subject`, `message`).
  - Shows success flash message (placeholder, no email service integrated yet).

## Registration and Login

- `GET/POST /register`
  - Register as `student` or `company`.
  - Validations:
    - required name/email/password
    - password length >= 6
    - password confirmation match
    - unique email
  - Auto-creates role profile record.
- `GET/POST /login`
  - Authenticates email + password.
  - Blocks inactive users.
- `GET /logout`
  - Logs out authenticated user.

## Student Features

- `GET /student`
  - Student landing page (student/admin access).
- `GET /student/dashboard`
  - Shows profile, applied jobs, and active jobs.
- `POST /student/profile`
  - Updates student profile fields:
    - `course`, `skills`, `bio`, `resume_link`
- `POST /student/apply/<job_id>`
  - Apply to active job.
  - Prevents duplicate apply.
  - Requires cover letter length >= 20.

## Company Features

- `GET /company`
  - Company landing page (company/admin access).
- `GET /company/dashboard`
  - Shows company profile, posted jobs, incoming applications.
- `POST /company/profile`
  - Updates company profile fields:
    - `company_name`, `industry`, `description`, `website`
- `POST /company/jobs/create`
  - Creates a new job posting.
  - Required: `title`, `description`, `location`
- `POST /company/jobs/<job_id>/toggle`
  - Company can activate/deactivate own jobs.
- `POST /company/applications/<app_id>/status`
  - Company updates application status.
  - Allowed values:
    - `pending`, `shortlisted`, `rejected`, `selected`

## Admin Features

- `GET /admin/dashboard`
  - Shows all users, jobs, applications, and platform stats.
- `POST /admin/users/<user_id>/toggle`
  - Activate/deactivate user account.
  - Safety: admin cannot deactivate own account.
- `POST /admin/jobs/<job_id>/toggle`
  - Admin can activate/deactivate any job.

## Current Limits / Notes

- Contact form currently only flashes success; no real mail sending.
- No file upload for resumes (resume uses link field).
- Basic flash-message validation only (no advanced form library).
- App runs with `debug=True` in local run mode.
