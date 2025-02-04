from flask import Blueprint, render_template, redirect, url_for, request, flash , session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from admin_app.admin import login_manager, db_admin
from werkzeug.security import check_password_hash
import pymongo
import os 
from dotenv import load_dotenv

load_dotenv()

from db.mongo_connection import get_mongo_connection 
# Admin Blueprint
admin_bp = Blueprint('admin_routes', __name__)


#admin connections
mongo_admin_uri = os.getenv("MONGO_URI_ADMIN")


# Use the correct collection reference
admin_collection = db_admin["Admin"]
# Admin User Model
class AdminUser(UserMixin):
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

# Load Admin User from Database
@login_manager.user_loader
def load_user(user_id):
    user_data = db_admin.Admin.find_one({"_id": user_id})
    if user_data:
        return AdminUser(user_id=user_data["_id"], username=user_data["username"], email=user_data["email"])
    return None

# Admin Login Route
@admin_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Find admin in MongoDB
        admin_data = db_admin.Admin.find_one({"email": email})

        if admin_data and check_password_hash(admin_data["password"], password):  # Werkzeug password verification
            admin = AdminUser(user_id=admin_data["_id"], username=admin_data["username"], email=admin_data["email"])
            login_user(admin)
            return redirect(url_for('admin_routes.admin_dashboard'))

        else:
            flash("Invalid credentials", "danger")

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