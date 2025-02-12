import random
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_mail import Message, Mail
from werkzeug.security import generate_password_hash
from main_app.db_config import main_collection, it_collection
from main_app.config import Config

mail = Mail()
reset_password_bp = Blueprint("reset_password_bp", __name__)

def generate_otp():
    """Generates a 6-digit OTP"""
    return str(random.randint(100000, 999999))

@reset_password_bp.route('/reset-password', methods=['GET', 'POST'])
def request_reset():
    """User requests a password reset - OTP is sent"""
    if request.method == 'POST':
        email = request.form['email']

        # ✅ Check if email exists in MAIN or IT collections
        user = main_collection.find_one({"email": email}) or it_collection.find_one({"email": email})

        if not user:
            flash("No account found with that email.", "danger")
            return redirect(url_for('reset_password_bp.request_reset'))

        # ✅ Generate OTP and store it temporarily
        otp = generate_otp()
        session['reset_otp'] = otp
        session['reset_email'] = email  # Store email in session

        # ✅ Send OTP via email
        send_otp_email(email, otp)

        flash("An OTP has been sent to your email.", "info")
        return redirect(url_for('reset_password_bp.verify_otp'))

    return render_template('Main/request_reset.html')

def send_otp_email(email, otp):
    """Sends OTP to the user's email"""
    msg = Message("Your Password Reset OTP",
                  sender="your-email@gmail.com",
                  recipients=[email])
    msg.body = f"Your OTP for password reset is: {otp}\nThis OTP is valid for 5 minutes."
    mail.send(msg)

@reset_password_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """User enters OTP to reset password"""
    if request.method == 'POST':
        entered_otp = request.form['otp']

        # ✅ Check if OTP is correct
        if entered_otp == session.get('reset_otp'):
            return redirect(url_for('reset_password_bp.reset_password'))  # ✅ Redirect to reset password page

        flash("Invalid OTP. Please try again.", "danger")
        return redirect(url_for('reset_password_bp.verify_otp'))

    return render_template('Main/verify_otp.html')

@reset_password_bp.route('/reset-password-final', methods=['GET', 'POST'])
def reset_password():
    """User sets a new password after OTP verification"""
    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed_password = generate_password_hash(new_password)

        email = session.get('reset_email')  # Get email from session
        if not email:
            flash("Session expired. Please request a new OTP.", "danger")
            return redirect(url_for('reset_password_bp.request_reset'))

        # ✅ Update password in the correct collection
        if main_collection.find_one({"email": email}):
            main_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
        elif it_collection.find_one({"email": email}):
            it_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})
        else:
            flash("User not found.", "danger")
            return redirect(url_for('reset_password_bp.request_reset'))

        # ✅ Clear session data
        session.pop('reset_otp', None)
        session.pop('reset_email', None)

        flash("Your password has been updated! You can now log in.", "success")
        return redirect(url_for('login_bp.login'))

    return render_template('Main/reset_password.html')
