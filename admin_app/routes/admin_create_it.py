import random
import string
import pymongo
import smtplib
from email.message import EmailMessage
from flask import Blueprint, request, render_template, flash, redirect, url_for
from werkzeug.security import generate_password_hash
import os
from main_app.db_config import it_collection

admin_create_it_bp = Blueprint("admin_create_it_bp", __name__)

# ✅ Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

def generate_unique_it_id():
    """Generate a unique IT User ID in the format ITXXXXXX@hiresync.com"""
    while True:
        unique_id = "IT" + "".join(random.choices(string.digits, k=6)) + "@hiresync.com"
        if not it_collection.find_one({"user_id": unique_id}):
            return unique_id

def generate_random_password(length=8):
    """Generate a secure random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return "".join(random.choices(characters, k=length))

def send_email(user_email, user_id, temp_password, assigned_equipment):
    """Send an email to the IT user with login credentials and assigned equipment"""
    msg = EmailMessage()
    msg["Subject"] = "Your HireSync IT Account & Assigned Equipment"
    msg["From"] = EMAIL_SENDER
    msg["To"] = user_email

    equipment_list = "\n".join(assigned_equipment) if assigned_equipment else "No equipment assigned."

    msg.set_content(f"""
    Hello IT Team Member,

    Your account has been created successfully.

    ✅ IT User ID: {user_id}
    ✅ Temporary Password: {temp_password}

    Assigned Equipment:
    {equipment_list}

    Please log in using your IT User ID and change your password immediately.

    Regards,  
    HireSync Admin Team
    """)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"📩 Email sent successfully to {user_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

@admin_create_it_bp.route('/create_it', methods=['GET', 'POST'])
def create_it():
    """Allow Admin to create an IT user and assign equipment"""
    if request.method == 'POST':
        email = request.form.get("email").strip().lower()
        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        selected_equipment = request.form.getlist("equipment")  # ✅ Get list of selected equipment

        # ✅ Check if email already exists
        if it_collection.find_one({"email": email}):
            flash("❌ An IT user with this email already exists.", "danger")
            return redirect(url_for("admin_create_it_bp.create_it"))

        # ✅ Generate unique IT User ID and password
        user_id = generate_unique_it_id()
        temp_password = generate_random_password()
        hashed_password = generate_password_hash(temp_password)

        # ✅ IT User Data with Assigned Equipment
        it_user_data = {
            "user_id": user_id,
            "email": email,
            "password": hashed_password,
            "role": "IT",
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

        # ✅ Insert IT User into MongoDB
        it_collection.insert_one(it_user_data)

        # ✅ Send Email with Credentials and Assigned Equipment
        send_email(email, user_id, temp_password, selected_equipment)

        flash(f"✅ IT User Created Successfully! IT User ID: {user_id}, Temporary Password: {temp_password}", "success")
        return redirect(url_for("admin_routes.admin_dashboard"))

    return render_template("admin/create_it.html")
