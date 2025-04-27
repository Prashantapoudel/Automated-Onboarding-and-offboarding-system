from flask import Blueprint, render_template, redirect, url_for, session
from main_app.main_app import login_manager, db_main 
from flask_login import login_required ,logout_user, current_user

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():

 pages = [
    (url_for('file_upload_bp.upload_onboarding_file'), 'submit.png', 'Document Uploads'),
    (url_for('file_upload_bp.view_onboarding_files'), 'onboarding.png', 'Onboarding Paperwork'),
    (url_for('file_upload_bp.view_offboarding_files'), 'offboarding.png', 'Offboarding Paperwork'),
    (url_for('file_upload_bp.upload_offboarding_file_user'), 'submit.png', 'Upload Offboarding File'),  # ✅ New
    ('/profile', 'edit.png', 'Edit Profile'),
    ('/rule', 'rules.png', 'Company Rules'),
    ('https://app.hotschedules.com/hs/login.jsp?continue=%2FmenuParser.hs%3Fscreen%3DemployeeHome%26firstTime%3Dtrue', 'schedule.png', 'HotSchedules'),
    ('/messages', 'rules.png', 'Messages'),
    ('https://whatfix.com/blog/types-employee-training-programs/', 'training.png', 'Schoox Training'),
    (url_for('exit_interview_bp.user_exit_interview'), 'interview.png', 'Exit Interview'),
    (url_for('exit_interview_bp.view_payroll'), 'salary.png', 'User Payroll'),
    (url_for('main_task_bp.my_tasks'), 'onboarding.png', 'My Tasks')  # ✅ New
]


 return render_template('main/dashboard.html', pages=pages)



@user_bp.route("/check-session")
def check_session():
    session["test"] = "Session Works!"
    return f"Session Data: {session.get('test')}"

@user_bp.route('/overview')
@login_required
def overview():
    return render_template('main/Overview.html',user=current_user )

@user_bp.route('/policies')
@login_required
def policies():
    return render_template('main/Policies.html',user=current_user)

@user_bp.route('/history')
@login_required
def history():
    return render_template('main/History.html',user=current_user)

@user_bp.route('/rule')
@login_required
def rule():
    return render_template('main/rule.html',user=current_user)



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
