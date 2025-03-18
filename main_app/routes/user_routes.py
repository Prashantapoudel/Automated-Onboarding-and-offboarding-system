from flask import Blueprint, render_template, redirect, url_for, session
from main_app.main_app import login_manager, db_main 
from flask_login import login_required ,logout_user

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('main/dashboard.html')

@user_bp.route("/check-session")
def check_session():
    session["test"] = "Session Works!"
    return f"Session Data: {session.get('test')}"

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    response = redirect(url_for('login_bp.login'))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
