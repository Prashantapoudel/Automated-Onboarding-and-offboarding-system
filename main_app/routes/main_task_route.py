from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bson.objectid import ObjectId
from datetime import datetime
from main_app.db_config import work_assignment_collection, main_collection, it_collection, admin_collection

main_task_bp = Blueprint("main_task_bp", __name__)

def get_display_name(user_id):
    user_data = main_collection.find_one({"user_id": user_id}) or \
                it_collection.find_one({"user_id": user_id}) or \
                admin_collection.find_one({"user_id": user_id})

    if user_data:
        first_name = user_data.get("profile", {}).get("name", {}).get("first_name")
        last_name = user_data.get("profile", {}).get("name", {}).get("last_name")

        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
    return user_id

@main_task_bp.route('/my_tasks', methods=['GET'])
@login_required
def my_tasks():
    user_id = current_user.id
    my_tasks = list(work_assignment_collection.find({"assigned_to_id": user_id}).sort("created_at", 1))

    for task in my_tasks:
        task["assigned_by_name"] = get_display_name(task.get("assigned_by_id"))
        task["assigned_to_name"] = get_display_name(task.get("assigned_to_id"))

    return render_template("main/my_tasks.html", tasks=my_tasks)

@main_task_bp.route('/update_task_status/<task_id>', methods=['POST'])
@login_required
def update_task_status(task_id):
    user_id = current_user.id
    task = work_assignment_collection.find_one({"_id": ObjectId(task_id)})

    if task and task.get("assigned_to_id") == user_id:
        new_status = request.form['status']
        work_assignment_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": new_status}}
        )
        flash("Task status updated.", "success")
    else:
        flash("Unauthorized or task not found.", "danger")

    return redirect(url_for('main_task_bp.my_tasks'))
