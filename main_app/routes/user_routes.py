from flask import Blueprint, render_template
from main_app.main_app import login_manager, db_main 

user_bp = Blueprint('user_routes', __name__)

@user_bp.route('/dashboard')
def user_dashboard():
    return render_template('main/dashboard.html', user_name="Employee")
@user_bp.route('/test')
def test_page():
    return "<h1>Flask is Working! 🚀</h1>"
