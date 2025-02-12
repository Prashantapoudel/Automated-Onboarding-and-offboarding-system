from flask import Blueprint, render_template, redirect, url_for, request, flash , session,Flask
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from admin_app.admin import login_manager, db_admin
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from admin_app.models.admin_model import AdminUser
from dotenv import load_dotenv
from flask_mail import Mail, Message
import os
from itsdangerous import URLSafeTimedSerializer
import smtplib
from admin_app import app, mail 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from admin_app.admin import app, mail

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
import random
from datetime import datetime, timedelta
mail = Mail()

def configure_mail(app):
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # ✅ Use your email provider
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")  # ✅ Ensure this is set in .env
    app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")  # ✅ Ensure this is set in .env
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("EMAIL_USER")
    app.config['MAIL_SUPPRESS_SEND'] = False
    app.config['MAIL_USE_SSL'] = False 

    
print("✅ Flask-Mail Configured:",os.getenv("EMAIL_USER"))




@admin_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        admin_data = db.Admin.find_one({"email": email})

        if admin_data:
            # ✅ Step 1: Generate OTP
            otp = str(random.randint(100000, 999999))  # Generates a 6-digit OTP

            # ✅ Step 2: Store OTP & Expiry in MongoDB
            expiration_time = datetime.utcnow() + timedelta(minutes=5)  # OTP valid for 5 minutes
            db.Admin.update_one({"email": email}, {"$set": {"otp": otp, "otp_expiration": expiration_time}})

            # ✅ Step 3: Send OTP via Email
            msg = MIMEMultipart()
            msg["From"] = os.getenv("EMAIL_USER")
            msg["To"] = email
            msg["Subject"] = "Your Password Reset OTP"

            msg.attach(MIMEText(f"Your OTP for password reset is: {otp}\nThis OTP is valid for 5 minutes."))

            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
                server.sendmail(os.getenv("EMAIL_USER"), email, msg.as_string())
                server.quit()

                flash("An OTP has been sent to your email.", "info")
                return redirect(url_for('admin_routes.verify_otp', email=email))

            except Exception as e:
                flash(f"Error sending email: {str(e)}", "danger")

        else:
            flash("Email not found. Please enter a registered email.", "danger")

    return render_template('admin/reset_password_request.html')

@admin_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    print("DEBUG: verify_otp route accessed")  # ✅ Debugging

    # ✅ Get email from form (POST) or request args (GET)
    email = request.form.get('email') or request.args.get('email')
    entered_otp = request.form.get('otp')

    # print(f"DEBUG: Email received: {email}")
    # print(f"DEBUG: OTP entered: {entered_otp}")

    if not email:
        flash("Email is missing. Please request a new reset link.", "danger")
        return redirect(url_for('admin_routes.reset_password_request'))

    # ✅ Retrieve user from MongoDB
    user_data = db.Admin.find_one({"email": email})
    
    if not user_data:
        print("DEBUG: User not found in the database")
        flash("Email not found. Please request a new reset link.", "danger")
        return redirect(url_for('admin_routes.reset_password_request'))

    stored_otp = user_data.get("otp")

    # print(f"DEBUG: Stored OTP in DB: {stored_otp}")

    if stored_otp and entered_otp and stored_otp == entered_otp:
        print(f"DEBUG: OTP verified successfully for {email}")
        flash("OTP verified! Please set a new password.", "success")

        # ✅ Pass email via URL instead of session
        return redirect(url_for('admin_routes.reset_password', email=email))
    else:
        # print("DEBUG: Invalid OTP entered or missing OTP input")
        flash("Invalid OTP. Please try again!", "danger")

    return render_template('admin/verify_otp.html', email=email)

# @admin_bp.route('/reset-password', methods=['GET', 'POST'])
# def reset_password_request():
#     if request.method == 'POST':
#         email = request.form['email']
#         admin_data = db.Admin.find_one({"email": email})

#         if admin_data:
#             serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))
#             token = serializer.dumps(email, salt='email-confirm')

#             verification_link = url_for('admin_routes.verify_email', token=token, _external=True)
            
#             msg = Message("Reset Your Password", sender=(os.getenv("EMAIL_USER")), recipients=[email])
#             msg.body = f"Click the link below to verify your email and reset your password:\n{verification_link}"
#             # mail.send(msg)
#             #THIS IS CUSTOM FROM HERE TO 
#             msg = MIMEMultipart()
#             msg["From"] = (os.getenv("EMAIL_USER"))
#             msg["To"] = email
#             msg["Subject"] = "Reset Your Password"
#             msg.attach(MIMEText( f"Click the link below to verify your email and reset your password:\n{verification_link}"))
#             server = smtplib.SMTP("smtp.gmail.com", 587)
#             server.ehlo()
#             server.starttls()  # Secure connection
#             server.ehlo()
#             server.login((os.getenv("EMAIL_USER")), (os.getenv("EMAIL_PASS")))  # Authenticate
#             server.sendmail((os.getenv("EMAIL_USER")), email, msg.as_string())  # Send email
#             server.quit()

#             #TO HERE
#             flash("A password reset link has been sent to your email.", "info")
#             return redirect(url_for('admin_routes.login'))
#         else:
#             flash("Email not found. Please enter a registered email.", "danger")

#     return render_template('admin/reset_password_request.html')
# @admin_bp.route('/verify-email/<token>', methods=['GET'])
# def verify_email(token):
#     try:
#         serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))
#         email = serializer.loads(token, salt="password-reset", max_age=3600)  # Token expires in 1 hour

#         # Find the user with this email
#         user = db.Admin.find_one({"email": email})
#         if not user:
#             flash("Invalid or expired token!", "danger")
#             return redirect(url_for('admin_routes.login'))

#         # ✅ Redirect to a password reset page with email verified
#         return redirect(url_for('admin_routes.reset_password', token=token))

#     except Exception as e:
#         flash("The reset link is invalid or has expired!", "danger")
#         return redirect(url_for('admin_routes.login'))

@admin_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    print("DEBUG: reset_password route is being accessed")  # ✅ Debugging

    # ✅ Get email from URL parameters
    email = request.args.get('email')
    print(f"DEBUG: Email received in reset_password: {email}")

    if not email:
        flash("Session expired. Please request a new reset.", "danger")
        return redirect(url_for('admin_routes.reset_password_request'))  # ✅ Redirect to reset request

    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = generate_password_hash(new_password)

        # ✅ Update password in MongoDB and remove OTP
        db.Admin.update_one({"email": email}, {"$set": {"password": hashed_password, "otp": None}})

        flash("Password reset successful! You can now login with your new password.", "success")
        return redirect(url_for('admin_routes.login'))

    return render_template('admin/reset_password.html', email=email)  # ✅ Pass email to template
