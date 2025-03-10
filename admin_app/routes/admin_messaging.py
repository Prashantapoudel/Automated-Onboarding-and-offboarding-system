from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from admin_app.config import messages_collection
from utils.user_utils import get_all_users  # ✅ Use same function
from datetime import datetime

admin_messaging_bp = Blueprint("admin_messaging_bp", __name__)

@admin_messaging_bp.route('/admin/messages', methods=['GET', 'POST'])
@login_required
def admin_send_message():
    """Allow Admin to message IT and Users."""
    
    all_users = get_all_users()  # ✅ Reuse the function

    if request.method == 'POST':
        recipient_id = request.form.get("recipient_id").strip()
        message_text = request.form.get("message_text").strip()

        if not recipient_id or not message_text:
            flash("Recipient and message cannot be empty!", "danger")
            return redirect(url_for("admin_messaging_bp.admin_send_message"))

        message_data = {
            "sender_id": current_user.user_id,
            "sender_role": current_user.role,
            "recipient_id": recipient_id,
            "message_text": message_text,
            "timestamp": datetime.utcnow()
        }

        messages_collection.insert_one(message_data)
        flash("Message sent successfully!", "success")

    messages = list(messages_collection.find({
        "$or": [
            {"sender_id": current_user.user_id},
            {"recipient_id": current_user.user_id}
        ]
    }).sort("timestamp", -1))

    return render_template("Admin/admin_messaging.html", messages=messages, users=all_users)
