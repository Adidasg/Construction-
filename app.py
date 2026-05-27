import os
import re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default-dev-secret-key-129381')

# Configure Database URI
db_url = os.environ.get('DATABASE_URL', 'sqlite:///project.db')
# Render's database URL format starts with postgres://, which SQLAlchemy no longer supports
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model for Quotations
class Quotation(db.Model):
    __tablename__ = 'quotations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Quotation {self.id} - {self.email}>'

# Create database tables if they do not exist
with app.app_context():
    db.create_all()

# ── Admin Auth Decorator ──────────────────────────────────────────────────────
def admin_required(f):
    """Decorator: redirects to login if admin session is not set."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin area.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ── Public Routes ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Server-side validation
        if not name or not email or not subject or not message:
            flash('All fields are required.', 'error')
            return redirect(url_for('contact'))

        if len(name) > 100 or len(email) > 120 or len(subject) > 50 or len(message) > 2000:
            flash('Input lengths exceed maximum limit.', 'error')
            return redirect(url_for('contact'))

        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address format.', 'error')
            return redirect(url_for('contact'))

        # Secure ORM insert — parameterized queries prevent SQL injection
        try:
            new_quotation = Quotation(name=name, email=email, subject=subject, message=message)
            db.session.add(new_quotation)
            db.session.commit()
            flash('Your quotation request was submitted successfully!', 'success')
        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again later.', 'error')

        return redirect(url_for('contact'))
    return render_template('contact.html')

# ── Admin Routes ──────────────────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page — credentials stored as environment variables."""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'changeme123')

        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            session.permanent = False          # Session expires on browser close
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard — shows all quotation submissions."""
    page     = request.args.get('page', 1, type=int)
    per_page = 20
    quotes   = Quotation.query.order_by(Quotation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('admin_dashboard.html', quotes=quotes)

@app.route('/admin/logout')
@admin_required
def admin_logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

