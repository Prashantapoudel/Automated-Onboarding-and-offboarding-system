import random
import string
import pymongo
import smtplib
from email.message import EmailMessage
from flask import Blueprint, request, render_template, flash, redirect, url_for
from werkzeug.security import generate_password_hash
import os
from main_app.db_config import main_collection

it_create_user_bp = Blueprint("it_create_user_bp", __name__)

# ✅ Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

def generate_unique_user_id():
    """Generate a unique User ID in the format UXXXXXX@hiresync.com"""
    while True:
        unique_id = "U" + "".join(random.choices(string.digits, k=6)) + "@hiresync.com"
        if not main_collection.find_one({"user_id": unique_id}):
            return unique_id

def generate_random_password(length=8):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choices(characters, k=length))

def send_email(user_email, user_id, temp_password, assigned_equipment):
    """Send an email to the user with their login credentials and assigned equipment"""
    msg = EmailMessage()
    msg["Subject"] = "Your HireSync Account & Assigned Equipment"
    msg["From"] = EMAIL_SENDER
    msg["To"] = user_email

    equipment_list = "\n".join(assigned_equipment) if assigned_equipment else "No equipment assigned."

    msg.set_content(f"""
    Hello,

    Your account has been created successfully.

    ✅ User ID: {user_id}
    ✅ Temporary Password: {temp_password}

    Assigned Equipment:
    {equipment_list}

    Please log in using your User ID and change your password immediately.

    Regards,  
    HireSync Team
    """)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📩 Email sent successfully to {user_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

@it_create_user_bp.route('/create_user', methods=['GET', 'POST'])
def create_user():
    """Allow IT to create a user and assign equipment"""
    if request.method == 'POST':
        email = request.form.get("email").strip().lower()
        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        selected_equipment = request.form.getlist("equipment")  # ✅ Get list of selected equipment

        # ✅ Check if email already exists
        if main_collection.find_one({"email": email}):
            flash("❌ A user with this email already exists.", "danger")
            return redirect(url_for("it_create_user_bp.create_user"))

        # ✅ Generate unique user ID and password
        user_id = generate_unique_user_id()
        temp_password = generate_random_password()
        hashed_password = generate_password_hash(temp_password)

        # ✅ User Data with Assigned Equipment
        user_data = {
            "user_id": user_id,
            "email": email,
            "password": hashed_password,
            "role": "MAIN",
            "profile": {
                "name": {
                    "first_name": first_name,
                    "last_name": last_name
                },
                "contact_details": {
                    "email": email
                },
                "equipment_assigned": selected_equipment  # ✅ Store assigned equipment
            },
            "temp_password": True
        }

        # ✅ Insert User into MongoDB
        main_collection.insert_one(user_data)

        # ✅ Send Email with Credentials and Assigned Equipment
        send_email(email, user_id, temp_password, selected_equipment)

        flash(f"✅ User Created Successfully! User ID: {user_id}, Temporary Password: {temp_password}", "success")
        return redirect(url_for("it_bp.it_dashboard"))

    return render_template("Main/create_user.html")
