from __future__ import annotations

import os
from datetime import datetime
from functools import wraps
import re

import google.generativeai as genai
from pypdf import PdfReader

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'replace-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///campus_bridge.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.jinja_env.add_extension('jinja2.ext.do')

# Expose recommendation logic to templates
def get_match_score(student, job):
    if not student.student_profile or not job.ai_requirements:
        return 0
    student_skills = student.student_profile.ai_skills.split(',') if student.student_profile.ai_skills else []
    job_skills = job.ai_requirements.split(',') if job.ai_requirements else []
    
    if not student_skills and student.student_profile.skills:
        # Fallback to manual skills if AI analysis hasn't run yet or failed
        student_skills = [s.strip().lower() for s in student.student_profile.skills.split(',')]
    
    return calculate_match_score(student_skills, job_skills)

app.jinja_env.globals.update(get_match_score=get_match_score)

def get_skills_gap(student, job):
    if not student.student_profile or not job.ai_requirements:
        return {"matched": [], "missing": []}
    
    student_skills = [s.strip().lower() for s in (student.student_profile.ai_skills or student.student_profile.skills or "").split(',') if s.strip()]
    job_skills = [s.strip().lower() for s in job.ai_requirements.split(',') if s.strip()]
    
    matched = [s for s in job_skills if s in student_skills]
    missing = [s for s in job_skills if s not in student_skills]
    
    return {"matched": matched, "missing": missing}

app.jinja_env.globals.update(get_skills_gap=get_skills_gap)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Gemini AI Initialization
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyALWYwBaeGZ2Eic7QF0Qhb2nAM9yzNzlGo')
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def extract_text_from_pdf(filepath):
    """Extracts text from a PDF file efficiently."""
    try:
        if not os.path.exists(filepath):
            return ""
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

def analyze_with_ai(text, prompt_type="resume"):
    """Uses AI to extract skills and profile info from text."""
    if not text:
        return []
    
    prompts = {
        "resume": "Extract a comma-separated list of technical and soft skills from this resume text: ",
        "job": "Extract a comma-separated list of required skills and qualifications from this job description: ",
        "feedback": "As a professional finance career consultant, provide a concise (max 150 words) 3-point bulleted list of improvements for this resume, focusing on impact and industry keywords: "
    }
    
    try:
        response = model.generate_content(f"{prompts.get(prompt_type, prompts['resume'])}\n\n{text}")
        if prompt_type == "feedback":
            return response.text
        skills = [s.strip().lower() for s in response.text.split(',') if s.strip()]
        return skills
    except Exception as e:
        print(f"AI Analysis error: {e}")
        return "" if prompt_type == "feedback" else []

def calculate_match_score(student_skills, job_skills):
    """Calculates a simple match score between two sets of skills."""
    if not student_skills or not job_skills:
        return 0
    common = set(student_skills).intersection(set(job_skills))
    score = (len(common) / len(job_skills)) * 100 if job_skills else 0
    return min(int(score), 100)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    is_active_user = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return self.is_active_user


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    course = db.Column(db.String(120), default='CA Foundation / Inter / Final')
    skills = db.Column(db.Text, default='')
    bio = db.Column(db.Text, default='')
    resume_link = db.Column(db.String(300), default='')
    resume_path = db.Column(db.String(300), default='')
    ai_skills = db.Column(db.Text, default='') # Cached skills from resume
    resume_ai_feedback = db.Column(db.Text, default='') # AI career advice


class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(180), nullable=False)
    industry = db.Column(db.String(120), default='Accounting & Finance')
    description = db.Column(db.Text, default='')
    website = db.Column(db.String(300), default='')


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    stipend = db.Column(db.String(60), default='As per company policy')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    pdf_jd_path = db.Column(db.String(300), default='')
    ai_requirements = db.Column(db.Text, default='') # Cached skills from JD

    company = db.relationship('User', backref='jobs', foreign_keys=[company_id])


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    job = db.relationship('Job', backref='applications', foreign_keys=[job_id])
    student = db.relationship('User', backref='applications', foreign_keys=[student_id])

    __table_args__ = (db.UniqueConstraint('job_id', 'student_id', name='uq_job_student'),)


class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')]
    )
    role = SelectField(
        'Account Type', choices=[('student', 'Student'), ('company', 'Company')], validators=[DataRequired()]
    )
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter(func.lower(User.email) == email.data.lower()).first()
        if user:
            raise ValueError('An account with this email already exists.')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))


def role_required(*roles: str):
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def ensure_admin_exists() -> None:
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@cabridge.com').strip().lower()
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    admin = User.query.filter(func.lower(User.email) == admin_email).first()
    if admin:
        return

    admin = User(full_name='Platform Admin', email=admin_email, role='admin', is_active_user=True)
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()


@app.route('/')
def index():
    jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).all()
    return render_template('index.html', jobs=jobs)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/student')
@role_required('student', 'admin')
def student_page():
    return render_template('student.html')


@app.route('/company')
@role_required('company', 'admin')
def company_page():
    return render_template('company.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not subject or not message:
            flash('Please fill all required fields in the contact form.', 'warning')
            return redirect(url_for('contact'))

        # Placeholder handler; replace with mail service integration in production.
        flash('Thanks for contacting us. Our team will reach out soon.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            form.validate_email(form.email)
        except ValueError as e:
            flash(str(e), 'warning')
            return redirect(url_for('register'))

        user = User(full_name=form.full_name.data, email=form.email.data.lower(), role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if form.role.data == 'student':
            db.session.add(StudentProfile(user_id=user.id))
        else:
            db.session.add(CompanyProfile(user_id=user.id, company_name=form.full_name.data))

        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower(User.email) == form.email.data.lower()).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        if not user.is_active_user:
            flash('Your account is currently inactive. Contact admin.', 'warning')
            return redirect(url_for('login'))

        login_user(user)
        flash('Logged in successfully.', 'success')

        if user.role == 'student':
            return redirect(url_for('student_dashboard'))
        if user.role == 'company':
            return redirect(url_for('company_dashboard'))
        return redirect(url_for('admin_dashboard'))

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/student/dashboard')
@role_required('student')
def student_dashboard():
    profile = current_user.student_profile
    applications = (
        Application.query.filter_by(student_id=current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    available_jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).all()
    return render_template(
        'student_dashboard.html',
        profile=profile,
        applications=applications,
        jobs=available_jobs,
    )


@app.route('/student/profile', methods=['POST'])
@role_required('student')
def update_student_profile():
    profile = current_user.student_profile
    profile.course = request.form.get('course', '').strip()
    profile.skills = request.form.get('skills', '').strip()
    profile.bio = request.form.get('bio', '').strip()
    profile.resume_link = request.form.get('resume_link', '').strip()
    db.session.commit()
    flash('Student profile updated.', 'success')
    return redirect(url_for('student_dashboard'))


@app.route('/student/resume/upload', methods=['POST'])
@role_required('student')
def upload_resume():
    if 'resume' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('student_dashboard'))
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for('student_dashboard'))
    
    if file and allowed_file(file.filename):
        from werkzeug.utils import secure_filename
        filename = secure_filename(f"resume_{current_user.id}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        profile = current_user.student_profile
        profile.resume_path = os.path.join('uploads', filename).replace('\\', '/')
        
        # Trigger AI Analysis
        full_path = os.path.join(app.root_path, 'static', profile.resume_path)
        text = extract_text_from_pdf(full_path)
        
        # 1. Extract Skills
        ai_skills_list = analyze_with_ai(text, "resume")
        profile.ai_skills = ",".join(ai_skills_list)
        
        # 2. Get Career Feedback
        profile.resume_ai_feedback = analyze_with_ai(text, "feedback")
        
        db.session.commit()
        
        flash('Resume uploaded and AI analysis complete.', 'success')
        return redirect(url_for('student_dashboard'))
    
    flash('Invalid file type. Please upload a PDF or Doc.', 'danger')
    return redirect(url_for('student_dashboard'))


@app.route('/student/apply/<int:job_id>', methods=['POST'])
@role_required('student')
def apply_job(job_id: int):
    job = db.session.get(Job, job_id)
    if not job or not job.is_active:
        flash('Job is not available.', 'warning')
        return redirect(url_for('student_dashboard'))

    existing = Application.query.filter_by(job_id=job_id, student_id=current_user.id).first()
    if existing:
        flash('You have already applied for this job.', 'info')
        return redirect(url_for('student_dashboard'))

    cover_letter = request.form.get('cover_letter', '').strip()
    if len(cover_letter) < 20:
        flash('Cover letter must be at least 20 characters long.', 'danger')
        return redirect(url_for('student_dashboard'))

    application = Application(job_id=job_id, student_id=current_user.id, cover_letter=cover_letter)
    db.session.add(application)
    db.session.commit()
    flash('Application submitted.', 'success')
    return redirect(url_for('student_dashboard'))


@app.route('/company/dashboard')
@role_required('company')
def company_dashboard():
    profile = current_user.company_profile
    jobs = Job.query.filter_by(company_id=current_user.id).order_by(Job.created_at.desc()).all()
    applications = (
        Application.query.join(Job, Application.job_id == Job.id)
        .filter(Job.company_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return render_template('company_dashboard.html', profile=profile, jobs=jobs, applications=applications)


@app.route('/company/profile', methods=['POST'])
@role_required('company')
def update_company_profile():
    profile = current_user.company_profile
    profile.company_name = request.form.get('company_name', '').strip() or current_user.full_name
    profile.industry = request.form.get('industry', '').strip()
    profile.description = request.form.get('description', '').strip()
    profile.website = request.form.get('website', '').strip()
    db.session.commit()
    flash('Company profile updated.', 'success')
    return redirect(url_for('company_dashboard'))


@app.route('/company/jobs/create', methods=['POST'])
@role_required('company')
def create_job():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    location = request.form.get('location', '').strip()
    stipend = request.form.get('stipend', '').strip() or 'As per company policy'

    if not title or not description or not location:
        flash('Title, description, and location are required.', 'danger')
        return redirect(url_for('company_dashboard'))

    pdf_jd_path = ''
    if 'pdf_jd' in request.files:
        file = request.files['pdf_jd']
        if file and file.filename != '' and allowed_file(file.filename):
            from werkzeug.utils import secure_filename
            filename = secure_filename(f"jd_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            pdf_jd_path = os.path.join('uploads', filename).replace('\\', '/')
            
            # Trigger AI Analysis for JD
            text = extract_text_from_pdf(file_path)
            ai_req_list = analyze_with_ai(text, "job")
            ai_requirements = ",".join(ai_req_list)
        else:
            ai_requirements = ""

    job = Job(
        company_id=current_user.id, 
        title=title, 
        description=description, 
        location=location, 
        stipend=stipend,
        pdf_jd_path=pdf_jd_path,
        ai_requirements=ai_requirements
    )
    db.session.add(job)
    db.session.commit()
    flash('Job posted successfully.', 'success')
    return redirect(url_for('company_dashboard'))


@app.route('/company/jobs/<int:job_id>/toggle', methods=['POST'])
@role_required('company')
def toggle_job(job_id: int):
    job = db.session.get(Job, job_id)
    if not job or job.company_id != current_user.id:
        flash('Job not found.', 'warning')
        return redirect(url_for('company_dashboard'))

    job.is_active = not job.is_active
    db.session.commit()
    flash('Job status updated.', 'success')
    return redirect(url_for('company_dashboard'))


@app.route('/company/applications/<int:app_id>/status', methods=['POST'])
@role_required('company')
def update_application_status(app_id: int):
    application = db.session.get(Application, app_id)
    if not application or application.job.company_id != current_user.id:
        flash('Application not found.', 'warning')
        return redirect(url_for('company_dashboard'))

    status = request.form.get('status', '').strip().lower()
    if status not in {'pending', 'shortlisted', 'rejected', 'selected'}:
        flash('Invalid status.', 'danger')
        return redirect(url_for('company_dashboard'))

    application.status = status
    db.session.commit()
    flash('Application status updated.', 'success')
    return redirect(url_for('company_dashboard'))


@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    applications = Application.query.order_by(Application.created_at.desc()).all()
    stats = {
        'students': User.query.filter_by(role='student').count(),
        'companies': User.query.filter_by(role='company').count(),
        'admins': User.query.filter_by(role='admin').count(),
        'active_jobs': Job.query.filter_by(is_active=True).count(),
        'total_applications': Application.query.count(),
    }
    return render_template('admin_dashboard.html', users=users, jobs=jobs, applications=applications, stats=stats)


@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_user_status(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found.', 'warning')
        return redirect(url_for('admin_dashboard'))

    if user.role == 'admin' and user.id == current_user.id:
        flash('You cannot deactivate your own admin account.', 'danger')
        return redirect(url_for('admin_dashboard'))

    user.is_active_user = not user.is_active_user
    db.session.commit()
    flash('User status updated.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/jobs/<int:job_id>/toggle', methods=['POST'])
@role_required('admin')
def admin_toggle_job(job_id: int):
    job = db.session.get(Job, job_id)
    if not job:
        flash('Job not found.', 'warning')
        return redirect(url_for('admin_dashboard'))

    job.is_active = not job.is_active
    db.session.commit()
    flash('Job status updated by admin.', 'success')
    return redirect(url_for('admin_dashboard'))


with app.app_context():
    db.create_all()
    ensure_admin_exists()


if __name__ == '__main__':
    app.run(debug=True, reloader_type='stat')
