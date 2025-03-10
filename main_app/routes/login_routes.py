from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_user
from werkzeug.security import check_password_hash
from main_app.db_config import main_collection, it_collection
from main_app.models.user_models import UserModel
from main_app.models.it_models import ITModel

login_bp = Blueprint("login_bp", __name__)

@login_bp.route('/', methods=['GET', 'POST'])
def login():
    """Single login page for both IT & MAIN users"""
    if request.method == 'POST':
        user_id = request.form['user_id'].strip()  # ✅ Remove unwanted spaces
        password = request.form['password']

        print(f"🛠 DEBUG: Trying to login with user_id: '{user_id}'")  # Debug print

        # ✅ Print all users in MAIN collection for debugging
        print(f"🛠 DEBUG: Fetching all users in MAIN collection...")
        all_users = list(main_collection.find({}, {"user_id": 1}))
        # print(f"📌 DEBUG: Users in MAIN collection: {all_users}")

        # ✅ Check MAIN Collection First
        user_data = main_collection.find_one({"user_id": user_id})
        # print(f"🔍 DEBUG: Query result from MAIN collection: {user_data}")  # Print the result

        user_model = None  # To store the user model

        if user_data:
            # print(f"✅ DEBUG: Found user in MAIN collection: {user_data}")
            user_model = UserModel
        else:
            # print(f"❌ DEBUG: User not found in MAIN. Checking IT collection...")
            user_data = it_collection.find_one({"user_id": user_id})
            # print(f"🔍 DEBUG: Query result from IT collection: {user_data}")
            if user_data:
                user_model = ITModel
            # if user_data:
            #     # print(f"✅ DEBUG: Found user in IT collection: {user_data}")
            #     user_model = ITModel
            # else:
            #     print(f"❌ DEBUG: User not found in IT collection either!")

        if user_data:
            stored_password = user_data.get("password", "")
            # print(f"🔍 DEBUG: Stored password hash: {stored_password}")

            # ✅ Check if password is correct
            if check_password_hash(stored_password, password):
                # print(f"✅ DEBUG: Password match successful!")

                user = user_model(
                    user_id=user_data["user_id"],  
                    email=user_data.get("email", ""),         
                    role=user_data.get("role", "Unknown")
                )
                login_user(user)
                flash("Login successful!", "success")

                # ✅ Redirect based on role after password update
                if user_data.get("temp_password", True):  
                    flash("You must change your temporary password before proceeding.", "warning")
                    return redirect(url_for('change_password_bp.change_password_page'))

                if user.role == "IT":
                    return redirect(url_for('it_bp.it_dashboard'))
                elif user.role == "MAIN":
                    return redirect(url_for('user_bp.dashboard'))
                else:
                    return redirect(url_for('login_bp.login'))  # Default fallback
            else:
                # print(f"❌ DEBUG: Password does NOT match!")
                flash("Invalid User ID or Password", "danger")
        else:
            flash("Invalid User ID or Password", "danger")

    return render_template('main/login.html')  # ✅ Single login page
