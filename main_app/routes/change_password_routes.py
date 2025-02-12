from flask import Blueprint, request, render_template, flash, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_required, current_user
from main_app.db_config import main_collection, it_collection
from main_app.models.user_models import UserModel  # ✅ Import User Model for MAIN Users
from main_app.models.it_models import ITModel  # ✅ Import IT Model for IT Users

change_password_bp = Blueprint("change_password_bp", __name__)

@change_password_bp.route('/change-password-page', methods=['GET'])
@login_required
def change_password_page():
    """Render change password page for IT & MAIN users"""
    return render_template('main/change_password.html')

@change_password_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Allow IT & MAIN users to change their temporary password"""
    user_id = current_user.id  # ✅ Get logged-in user ID
    new_password = request.form.get("new_password")

    if not new_password:
        flash("Please enter a new password.", "danger")
        return redirect(url_for('change_password_bp.change_password_page'))

    hashed_new_password = generate_password_hash(new_password)

    # ✅ Determine whether user is MAIN or IT
    user_data = main_collection.find_one({"user_id": user_id})
    if user_data:
        collection = main_collection
        user_model = UserModel
    else:
        user_data = it_collection.find_one({"user_id": user_id})
        collection = it_collection
        user_model = ITModel

    if not user_data:
        flash("User not found!", "danger")
        return redirect(url_for('login_bp.login'))

    # ✅ Update password and remove `temp_password`
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"password": hashed_new_password, "temp_password": False}}
    )

    flash("Password changed successfully! Please log in again.", "success")
    return redirect(url_for('login_bp.login'))
