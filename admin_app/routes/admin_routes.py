from flask import Blueprint, render_template, redirect, url_for, request, flash , session,Flask
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from admin_app.admin import login_manager, db_admin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from admin_app.models.admin_model import AdminUser
from dotenv import load_dotenv
from flask_mail import Mail, Message
from admin_app import mail
import os
from itsdangerous import URLSafeTimedSerializer


load_dotenv()
app = Flask(__name__) 

from db.mongo_connection import get_mongo_connection 
# Admin Blueprint
admin_bp = Blueprint('admin_routes', __name__)


#admin connections
db = get_mongo_connection()


# Use the correct collection reference
admin_collection = db["Admin"]
# Admin User Model
class AdminUser(UserMixin):
    def __init__(self, user_id, email):
        self.id = user_id
        self.email = email

# Load Admin User from Database
@login_manager.user_loader
def load_user(user_id):
    user_data = db.Admin.find_one({"user_id": user_id})
    if user_data:
        return AdminUser(user_id=user_data["user_id"], email=user_data["email"])
    return None

# Admin Login Route
@admin_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        admin_data = admin_collection.find_one({"user_id": user_id})

        if admin_data and check_password_hash(admin_data["password"], password):  
            admin = AdminUser(
                user_id=admin_data["user_id"],  # Ensure this matches stored MongoDB field     
                email=admin_data.get("email", ""),         
            )
            login_user(admin)  # Logs in the admin user
            flash("Login successful!", "success")
            return redirect(url_for('admin_routes.admin_dashboard'))  # Ensure correct redirection

        else:
            flash("Invalid User ID or Password", "danger")

    return render_template('admin/login.html') 

# Logout Route
@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    response = redirect(url_for('admin_routes.login'))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if session.get("logged_out"):
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('admin_routes.login'))
    return render_template('admin/dashboard.html')



###   email password change 
mail = Mail()
import os
def configure_mail(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # ✅ Use your email provider
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")  # ✅ Ensure this is set in .env
    app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")  # ✅ Ensure this is set in .env
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("EMAIL_USER")
    app.config['MAIL_SUPPRESS_SEND'] = False

    
print("✅ Flask-Mail Configured:",os.getenv("EMAIL_USER"))
@admin_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        admin_data = db.Admin.find_one({"email": email})

        if admin_data:
            serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))
            token = serializer.dumps(email, salt='email-confirm')

            verification_link = url_for('admin_routes.verify_email', token=token, _external=True)
            
            msg = Message("Reset Your Password", sender=(os.getenv("EMAIL_USER")), recipients=[email])
            msg.body = f"Click the link below to verify your email and reset your password:\n{verification_link}"
            mail.send(msg)

            flash("A password reset link has been sent to your email.", "info")
            return redirect(url_for('admin_routes.login'))
        else:
            flash("Email not found. Please enter a registered email.", "danger")

    return render_template('admin/reset_password_request.html')
@admin_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))
        email = serializer.loads(token, salt="password-reset", max_age=3600)  # Token expires in 1 hour

        # Find the user with this email
        user = db.Admin.find_one({"email": email})
        if not user:
            flash("Invalid or expired token!", "danger")
            return redirect(url_for('admin_routes.login'))

        # ✅ Redirect to a password reset page with email verified
        return redirect(url_for('admin_routes.reset_password', token=token))

    except Exception as e:
        flash("The reset link is invalid or has expired!", "danger")
        return redirect(url_for('admin_routes.login'))

@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))
        email = serializer.loads(token, salt="password-reset", max_age=3600)

        if request.method == 'POST':
            new_password = request.form['password']
            hashed_password = generate_password_hash(new_password)
            db.Admin.update_one({"email": email}, {"$set": {"password": hashed_password}})

            flash("Password reset successful!", "success")
            return redirect(url_for('admin_routes.login'))

        return render_template('admin/reset_password.html', token=token)

    except Exception as e:
        flash("The reset link is invalid or has expired!", "danger")
        return redirect(url_for('admin_routes.login'))


