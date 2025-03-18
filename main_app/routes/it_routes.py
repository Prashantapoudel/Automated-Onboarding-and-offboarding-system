from flask import Blueprint, render_template, flash, redirect, url_for, session
from flask_login import login_required ,logout_user

it_bp = Blueprint('it_bp', __name__)


@it_bp.route('/it')
@login_required
def it_dashboard():
    return render_template('main/it_dashboard.html')
@it_bp.route("/check-session")
def check_session():
    session["test"] = "Session Works!"
    return f"Session Data: {session.get('test')}"

@it_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    response = redirect(url_for('login_bp.login'))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
