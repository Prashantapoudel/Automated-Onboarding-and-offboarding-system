from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from bson.objectid import ObjectId
from datetime import datetime
from main_app.db_config import work_assignment_collection, main_collection, it_collection, admin_collection
from utils.user_utils import get_all_users
task_bp = Blueprint("task_bp", __name__)

# Utility function to get current user id and role from session
def get_current_user():
    return session.get("id"), session.get("role")

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
    
    return user_id 

@task_bp.route('/assign_work', methods=['GET', 'POST'])
@login_required
def assign_work():
    user_id, role = get_current_user()

    all_users = get_all_users()
    assignable_users = []

    if role == "superuser":
        filtered_users = [u for u in all_users if u["user_id"] != user_id]  # Optional: don't show self
    elif role == "IT":
        filtered_users = [u for u in all_users if u["role"] == "User"]
    else:
        filtered_users = []
    
    for user in filtered_users:
        assignable_users.append({
            "user_id": user["user_id"],
            "role": user["role"],
            "display_name": get_display_name(user["user_id"])
    })


    for user in all_users:
        user['display_name'] = get_display_name(user['user_id'])
        assignable_users.append(user)

    selected_user = request.args.get("user_id", "").strip()

    if request.method == 'POST':
        assigned_to_id = request.form['assigned_to_id']
        title = request.form['title']
        description = request.form['description']
        deadline = request.form['deadline']

        # Determine role of the assigned user from DB
        assigned_user = main_collection.find_one({"user_id": assigned_to_id}) or \
                        it_collection.find_one({"user_id": assigned_to_id})
        assigned_to_role = assigned_user.get("role") if assigned_user else None

        if role == 'IT' and assigned_to_role != 'User':
            flash("IT can only assign work to Users.")
            return redirect(url_for('task_bp.assign_work', user_id=assigned_to_id))

        task_data = {
            "assigned_by_id": user_id,
            "assigned_by_role": role,
            "assigned_to_id": assigned_to_id,
            "assigned_to_role": assigned_to_role,
            "title": title,
            "description": description,
            "deadline": deadline,
            "status": "Pending",
            "created_at": datetime.utcnow()
        }

        work_assignment_collection.insert_one(task_data)
        flash("Work assigned successfully.")
        return redirect(url_for('task_bp.assign_work', user_id=assigned_to_id))

    return render_template('admin/assign_work.html', users=assignable_users, selected_user=selected_user)

@task_bp.route('/my_tasks', methods=['GET'])
@login_required
def my_tasks():
    user_id = session.get("id")
    role = session.get("role")

    status_filter = request.args.get("status")
    query = {} if not status_filter else {"status": status_filter}

    tasks = list(work_assignment_collection.find(query).sort("created_at", -1))

    for task in tasks:
        assigned_to_id = task.get("assigned_to_id")
        assigned_to_role = task.get("assigned_to_role")

        # Add assigned_to_name and type info regardless of role
        task["assigned_to_name"] = get_display_name(assigned_to_id)
        task["assigned_to_role"] = assigned_to_role

    return render_template("admin/my_tasks.html", tasks=tasks, selected_status=status_filter)

@task_bp.route('/update_task_status/<task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = work_assignment_collection.find_one({"_id": ObjectId(task_id)})

    if task:
        new_status = request.form['status']
        work_assignment_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": new_status}}
        )
        flash("Task status updated.", "success")
    else:
        flash("Task not found.", "danger")

    return redirect(url_for('task_bp.my_tasks'))
