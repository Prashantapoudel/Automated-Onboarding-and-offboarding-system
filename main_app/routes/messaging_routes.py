from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from main_app.db_config import messages_collection, main_collection, it_collection, admin_collection
from utils.user_utils import get_all_users
from datetime import datetime

messaging_bp = Blueprint("messaging_bp", __name__)


def get_display_name(user_id):
    """Retrieve the display name for a user based on available profile data."""
    user_data = main_collection.find_one({"user_id": user_id}) or it_collection.find_one({"user_id": user_id}) or admin_collection.find_one({"user_id": user_id})

    if user_data:
        first_name = user_data.get("profile", {}).get("name", {}).get("first_name")
        last_name = user_data.get("profile", {}).get("name", {}).get("last_name")

        if first_name and last_name:
            return f"{first_name} {last_name}"  # ✅ Show Full Name
        elif first_name:
            return first_name  # ✅ Show First Name only
    
    return user_id  # ❌ Fallback to User ID if no name found
@messaging_bp.route('/messages', methods=['GET', 'POST'])
@login_required
def send_message():
    """Allow Admin, IT, and Users to send messages and view them in a chat format."""
    
    all_users = get_all_users()  # ✅ Fetch all users for dropdown

    # ✅ Modify user list to include display names
    for user in all_users:
        user['display_name'] = get_display_name(user['user_id'])  # ✅ Apply display name function

    # ✅ Get selected recipient from dropdown
    selected_recipient = request.args.get("recipient_id", "").strip()


    if request.method == 'POST':
        recipient_id = request.form.get("recipient_id").strip()
        message_text = request.form.get("message_text").strip()

        if not recipient_id or not message_text:
            flash("Recipient and message cannot be empty!", "danger")
            return redirect(url_for("messaging_bp.send_message", recipient_id=recipient_id))

        message_data = {
            "sender_id": current_user.user_id,
            "recipient_id": recipient_id,
            "message_text": message_text,
            "timestamp": datetime.utcnow()
        }

        messages_collection.insert_one(message_data)  # ✅ Store message
        flash("Message sent successfully!", "success")
        return redirect(url_for("messaging_bp.send_message", recipient_id=recipient_id))  # ✅ Stay in selected chat

    # ✅ Fetch messages **only** between the logged-in user and the selected recipient
    messages = []
    if selected_recipient:
        messages = list(messages_collection.find({
            "$or": [
                {"sender_id": current_user.user_id, "recipient_id": selected_recipient},
                {"sender_id": selected_recipient, "recipient_id": current_user.user_id}
            ]
        }).sort("timestamp", 1))  # ✅ Sort messages in chronological order

        # ✅ Apply `get_display_name()` dynamically
        for message in messages:
            message["sender_name"] = get_display_name(message["sender_id"])
            message["recipient_name"] = get_display_name(message["recipient_id"])


    return render_template("main/messages.html", messages=messages, users=all_users, selected_recipient=selected_recipient)


