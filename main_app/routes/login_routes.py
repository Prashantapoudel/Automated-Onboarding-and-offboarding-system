from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_user
from werkzeug.security import check_password_hash
from main_app.db_config import main_collection, it_collection
from main_app.models.user_models import UserModel  # ✅ Import User Model for MAIN
from main_app.models.it_models import ITModel  # ✅ Import IT Model for IT

login_bp = Blueprint("login_bp", __name__)

@login_bp.route('/', methods=['GET', 'POST'])
def login():
    """Single login page for both IT & MAIN users"""
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']

        # ✅ Check MAIN Collection First
        user_data = main_collection.find_one({"user_id": user_id})
        user_model = None  # To store the user model

        # ✅ If not found, check IT Collection
        if not user_data:
            user_data = it_collection.find_one({"user_id": user_id})
            if user_data:
                user_model = ITModel  # ✅ Use IT model
        else:
            user_model = UserModel  # ✅ Use User model

        if user_data and check_password_hash(user_data["password"], password):
            user = user_model(
                user_id=user_data["user_id"],  # ✅ Ensure this matches MongoDB field
                email=user_data.get("email", ""),         
                role=user_data.get("role", "Unknown")
            )
            login_user(user)  # ✅ Logs in the user
            flash("Login successful!", "success")

            # ✅ Check if the user has a temporary password
            if user_data.get("temp_password", True):  # If temp_password = True (First Login)
                flash("You must change your temporary password before proceeding.", "warning")
                return redirect(url_for('change_password_bp.change_password_page'))

            # ✅ Redirect based on role after password update
            if user.role == "IT":
                return redirect(url_for('it_bp.it_dashboard'))
            elif user.role == "MAIN":
                return redirect(url_for('user_bp.user_dashboard'))
            else:
                return redirect(url_for('login_bp.login'))  # Default fallback

        flash("Invalid User ID or Password", "danger")

    return render_template('main/login.html')  # ✅ Single login page
