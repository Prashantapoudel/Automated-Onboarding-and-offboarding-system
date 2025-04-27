from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from main_app.db_config import exit_interviews_collection, main_collection, it_collection, admin_collection,payroll_collection
from utils.user_utils import get_all_users
from datetime import datetime
import smtplib, os
from bson import ObjectId
from email.mime.text import MIMEText

exit_interview_bp = Blueprint("exit_interview_bp", __name__)


def format_datetime(value):
    """Convert ISO datetime string to 'Month Day, Year - HH:MM AM/PM' format"""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%B %d, %Y - %I:%M %p")  # Example: "March 24, 2025 - 11:39 PM"
    except Exception:
        return value 
    
# ✅ Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

def send_email(to_email, subject, scheduled_date, body, ):
    """Send email notification with formatted date and UTF-8 encoding."""
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    formatted_date = format_datetime(scheduled_date)  # ✅ Format the date

    email_body = f"""
    Hello,

    {body}

     Scheduled Date: {formatted_date}

    Please be on time.

    Regards,  
    HireSync Team
    """

    msg = MIMEText(email_body, "plain", "utf-8")  # ✅ Use UTF-8 encoding
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            print("✅ Connecting to SMTP server...")
            server.login(sender_email, sender_password)
            print(f" Sending email to {to_email}...")
            server.sendmail(sender_email, to_email, msg.as_string())
            print(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        print(f"❌ Email send error: {e}")

def send_it_notification(it_emails, subject, body):
    """Send email notifications to all IT admins."""
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")

    msg = MIMEText(body, "plain", "utf-8")  # ✅ Use UTF-8 encoding
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = ", ".join(it_emails)  # ✅ Send to all IT admins

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            print("✅ Connecting to SMTP server...")
            server.login(sender_email, sender_password)
            print(f"📨 Sending email to IT admins: {', '.join(it_emails)}...")
            server.sendmail(sender_email, it_emails, msg.as_string())
            print("✅ IT Notification Sent Successfully")
    except Exception as e:
        print(f"❌ IT Email send error: {e}")

def get_user_email(user_id):
    """Retrieve the email address of a user based on user_id."""
    user = (
        main_collection.find_one({"user_id": user_id}) or
        it_collection.find_one({"user_id": user_id}) or
        admin_collection.find_one({"user_id": user_id})
    )
    return user["email"] if user and "email" in user else None

def get_display_name(user_id):
    """Retrieve the display name for a user based on available profile data."""
    user_data = (
        main_collection.find_one({"user_id": user_id}) or
        it_collection.find_one({"user_id": user_id}) or
        admin_collection.find_one({"user_id": user_id})
    )

    if user_data:
        first_name = user_data.get("profile", {}).get("name", {}).get("first_name")
        last_name = user_data.get("profile", {}).get("name", {}).get("last_name")

        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name

    return user_id  # ❌ Fallback to User ID if no name found


@exit_interview_bp.route("/schedule_exit_interview", methods=["GET", "POST"])
@login_required
def schedule_exit_interview():
    """IT schedules an exit interview for a user and sends an email notification."""
    users = get_all_users()

    for user in users:
        user["display_name"] = get_display_name(user["user_id"])

    if request.method == "POST":
        user_id = request.form.get("user_id").strip()
        schedule_date = request.form.get("schedule_date").strip()

        if not user_id or not schedule_date:
            flash("❌ All fields are required!", "danger")
            return redirect(url_for("exit_interview_bp.schedule_exit_interview"))

        exit_interviews_collection.insert_one({
            "user_id": user_id,
            "scheduled_date": schedule_date,
            "status": "Scheduled"
        })

        # ✅ Send Email Notification to User
        user_email = get_user_email(user_id)
        send_email(
    user_email,
    "Exit Interview Scheduled",
    schedule_date,  # ✅ This is the date
    "Your exit interview has been scheduled. Please check your dashboard for details."
)

        flash("✅ Exit interview scheduled successfully!", "success")
        return redirect(url_for("exit_interview_bp.schedule_exit_interview"))

    return render_template("main/schedule_exit_interview.html", users=users)


@exit_interview_bp.route('/request_reschedule', methods=['POST'])
@login_required
def request_reschedule():
    """Allow users to request a reschedule for their exit interview and notify IT."""
    user_id = current_user.user_id
    new_date = request.form.get("new_date")

    if not new_date:
        flash("❌ Please provide a new date and time.", "danger")
        return redirect(url_for("exit_interview_bp.user_exit_interview"))

    interview = exit_interviews_collection.find_one({"user_id": user_id})

    if not interview:
        flash("❌ No exit interview found to reschedule!", "danger")
        return redirect(url_for("exit_interview_bp.user_exit_interview"))

    # ✅ Update MongoDB with reschedule request
    exit_interviews_collection.update_one(
        {"user_id": user_id},
        {"$set": {"user_requested_change": {"new_date": new_date, "status": "Pending Approval"}}}
    )

    # ✅ Fetch IT Emails
    it_emails = [
        it_user["email"] for it_user in it_collection.find({}, {"email": 1}) if "email" in it_user
    ]

    if not it_emails:
        flash("❌ No IT Admin email found! IT won't be notified.", "warning")
        print("🔍 DEBUG: No IT emails found in MongoDB!")  # 🛠 Debugging log
        return redirect(url_for("exit_interview_bp.user_exit_interview"))

    # ✅ Get User Info
    user_email = get_user_email(user_id)
    user_name = get_display_name(user_id)

    # ✅ Format Dates for Readability
    formatted_current_date = format_datetime(interview.get("scheduled_date"))
    formatted_new_date = format_datetime(new_date)

    # ✅ Email Details
    subject = f" Exit Interview Reschedule Request - {user_name}"
    body = f"""
Hello IT Team,

{user_name} ({user_email}) has requested to reschedule their exit interview.

 **Current Date:** {formatted_current_date}  
 **Requested New Date:** {formatted_new_date} (Pending Approval)  

Please review the request and approve or decline accordingly.

Regards,  
HireSync System
"""

    # ✅ Send Email Notification to IT Admins
    for it_email in it_emails:
        send_it_notification(it_email,subject, body)  # ✅ Fixed argument order

    flash("✅ Reschedule request submitted! IT will review your request.", "success")
    return redirect(url_for("exit_interview_bp.user_exit_interview"))






@exit_interview_bp.route("/manage_exit_interviews", methods=["GET", "POST"])
@login_required
def manage_exit_interviews():
    """Allow IT/Admin to view, manage, approve/decline requests, and delete interviews."""

    # ✅ Fetch all exit interviews
    exit_interviews = list(exit_interviews_collection.find())

    # ✅ Fetch user data to map user_id -> Name
    all_users = list(main_collection.find({}, {"user_id": 1, "profile.name.first_name": 1, "profile.name.last_name": 1}))

    # ✅ Create a mapping {user_id: full_name}
    user_names = {
        user["user_id"]: f"{user.get('profile', {}).get('name', {}).get('first_name', '')} {user.get('profile', {}).get('name', {}).get('last_name', '')}".strip()
        for user in all_users
    }

    # ✅ Replace user_id with display name
    for interview in exit_interviews:
        interview["user_name"] = user_names.get(interview["user_id"], interview["user_id"])  # Fallback to user_id if name not found

    if request.method == "POST":
        interview_id = request.form.get("interview_id")
        action = request.form.get("action")

        interview = exit_interviews_collection.find_one({"_id": ObjectId(interview_id)})

        if interview:
            if action == "approve":
                # ✅ Ensure new_date exists before using it
                new_date = interview.get("user_requested_change", {}).get("new_date")

                if new_date:
                    # ✅ Approve Request
                    exit_interviews_collection.update_one(
                        {"_id": ObjectId(interview_id)},
                        {"$set": {
                            "scheduled_date": new_date,
                            "user_requested_change.status": "Approved"
                        }}
                    )

                    # ✅ Send Email Notification
                    user_email = get_user_email(interview["user_id"])
                    send_email(
                        user_email,
                        "Exit Interview Reschedule Approved",
                        new_date,
                        f"Your exit interview has been rescheduled to {new_date}."
                    )

                    flash("✅ Reschedule request approved!", "success")
                else:
                    flash("❌ No new date was requested!", "danger")

            elif action == "decline":
                # ✅ Decline Request
                exit_interviews_collection.update_one(
                    {"_id": ObjectId(interview_id)},
                    {"$set": {"user_requested_change.status": "Declined"}}
                )

                # ✅ Send Email Notification
                user_email = get_user_email(interview["user_id"])
                send_email(
                    user_email,
                    "Exit Interview Reschedule Declined",
                    interview["scheduled_date"],
                    "Your reschedule request was declined. Your interview will remain at the originally scheduled time."
                )

                flash("❌ Reschedule request declined!", "danger")

            elif action == "delete":
                # ✅ Delete Interview
                exit_interviews_collection.delete_one({"_id": ObjectId(interview_id)})
                flash("🗑️ Exit interview deleted successfully!", "info")

            return redirect(url_for("exit_interview_bp.manage_exit_interviews"))

    return render_template("main/manage_exit_interviews.html", exit_interviews=exit_interviews)



@exit_interview_bp.route('/user_exit_interview', methods=['GET'])
@login_required
def user_exit_interview():
    """Allow users to view their scheduled exit interview details."""
    interview = exit_interviews_collection.find_one({"user_id": current_user.user_id})

    if not interview:
        return render_template("main/user_exit_interview.html", interview=None)  # ✅ Pass None to handle no interviews

    return render_template("main/user_exit_interview.html", interview=interview)

@exit_interview_bp.route("/manage_payroll", methods=["GET", "POST"])
@login_required
def manage_payroll():
    """Allow IT to manage payroll data for employees."""
    users = get_all_users()  # ✅ Fetch all users

    for user in users:
        user["display_name"] = get_display_name(user["user_id"])

    if request.method == "POST":
        user_id = request.form.get("user_id")
        hours_worked = float(request.form.get("hours_worked"))
        hourly_rate = float(request.form.get("hourly_rate"))

        if not user_id or not hours_worked or not hourly_rate:
            flash("❌ All fields are required!", "danger")
            return redirect(url_for("exit_interview_bp.manage_payroll"))

        total_pay = hours_worked * hourly_rate
        pay_date = datetime.now().strftime("%Y-%m-%d")  # ✅ Store the current date

        payroll_data = {
            "user_id": user_id,
            "hours_worked": hours_worked,
            "hourly_rate": hourly_rate,
            "total_pay": total_pay,
            "pay_date": pay_date
        }

        # ✅ Update payroll record if user already has one
        payroll_collection.update_one(
            {"user_id": user_id},
            {"$set": payroll_data},
            upsert=True
        )

        flash(f"✅ Payroll updated for {get_display_name(user_id)}!", "success")
        return redirect(url_for("exit_interview_bp.manage_payroll"))

    # ✅ Fetch all payroll records
    payroll_data = list(payroll_collection.find())

    return render_template("main/manage_payroll.html", users=users, payroll_data=payroll_data)

@exit_interview_bp.route("/delete_payroll/<payroll_id>", methods=["POST"])
@login_required
def delete_payroll(payroll_id):
    """Delete a payroll record."""
    payroll_collection.delete_one({"_id": ObjectId(payroll_id)})
    flash("🗑️ Payroll record deleted successfully!", "info")
    return redirect(url_for("exit_interview_bp.manage_payroll"))

@exit_interview_bp.route("/view_payroll", methods=["GET"])
@login_required
def view_payroll():
    """Allow users to view their payroll details."""
    payroll = payroll_collection.find_one({"user_id": current_user.user_id})

    if not payroll:
        flash("❌ No payroll record found.", "danger")
        return redirect(url_for("user_bp.dashboard"))

    return render_template("main/user_payroll.html", payroll=payroll)





@exit_interview_bp.route("/manage_payroll", methods=["GET", "POST"])
@login_required
def manage_payroll():
    """Allow IT to manage payroll data for employees."""
    users = get_all_users()  # ✅ Fetch all users

    for user in users:
        user["display_name"] = get_display_name(user["user_id"])
    if request.method == "POST":
        user_id = request.form.get("user_id")
        user_name = get_display_name(user_id)
        hours_worked = float(request.form.get("hours_worked"))
        hourly_rate = float(request.form.get("hourly_rate"))

        if not user_id or not hours_worked or not hourly_rate:
            flash("❌ All fields are required!", "danger")
            return redirect(url_for("exit_interview_bp.manage_payroll"))

        total_pay = hours_worked * hourly_rate
        pay_date = datetime.now().strftime("%Y-%m-%d")  # ✅ Store the current date

        payroll_data = {
            "user_id": user_id,
            "hours_worked": hours_worked,
            "hourly_rate": hourly_rate,
            "total_pay": total_pay
        }

        # ✅ Prevent overriding the original pay_date
        payroll_collection.update_one(
            {"user_id": user_id},
            {"$set": payroll_data, "$setOnInsert": {"pay_date": pay_date}},
            upsert=True
        )

        flash(f"✅ Payroll updated for {get_display_name(user_id)}!", "success")
        return redirect(url_for("exit_interview_bp.manage_payroll"))

    # ✅ Fetch all payroll records
    payroll_data = list(payroll_collection.find())

    return render_template("main/manage_payroll.html", users=users, payroll_data=payroll_data)

@exit_interview_bp.route("/delete_payroll/<payroll_id>", methods=["POST"])
@login_required
def delete_payroll(payroll_id):
    """Delete a payroll record safely."""
    payroll_record = payroll_collection.find_one({"_id": ObjectId(payroll_id)})

    if not payroll_record:
        flash("❌ Payroll record not found!", "danger")
        return redirect(url_for("exit_interview_bp.manage_payroll"))

    payroll_collection.delete_one({"_id": ObjectId(payroll_id)})
    flash("🗑️ Payroll record deleted successfully!", "info")
    return redirect(url_for("exit_interview_bp.manage_payroll"))

@exit_interview_bp.route("/view_payroll", methods=["GET"])
@login_required
def view_payroll():
    """Allow users to view their payroll details with default values."""
    payroll = payroll_collection.find_one({"user_id": current_user.user_id})

    if not payroll:
        payroll = {
            "user_id": current_user.user_id,
            "hours_worked": 0,
            "hourly_rate": 0,
            "total_pay": 0,
            "pay_date": "N/A"
        }
        flash("⚠️ No payroll data found. Displaying default values.", "warning")

    return render_template("main/user_payroll.html", payroll=payroll)