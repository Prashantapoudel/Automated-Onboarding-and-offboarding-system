from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from main_app.db_config import it_payroll_collection, it_collection,main_collection, payroll_collection
from bson.objectid import ObjectId 

admin_payroll_bp = Blueprint("admin_payroll_bp", __name__)

@admin_payroll_bp.route('/manage_it_payroll', methods=['GET'])
@login_required
def manage_it_payroll():
    """Allow Admin to view all IT staff payrolls"""
    
    # Fetch all IT staff
    it_staff = list(it_collection.find({}, {"user_id": 1, "profile.name.first_name": 1, "profile.name.last_name": 1}))

    # Fetch all payroll data
    payroll_data = list(it_payroll_collection.find({}))

    return render_template("admin/manage_it_payroll.html", it_staff=it_staff, payroll_data=payroll_data)

@admin_payroll_bp.route('/update_it_payroll/<payroll_id>', methods=['GET', 'POST'])
@login_required
def update_it_payroll(payroll_id):
    """Allow Admin to update IT payroll"""
    
    payroll_record = it_payroll_collection.find_one({"_id": payroll_id})
    
    if not payroll_record:
        flash("❌ Payroll record not found!", "danger")
        return redirect(url_for("admin_payroll_bp.manage_it_payroll"))

    if request.method == "POST":
        hours_worked = request.form.get("hours_worked")
        hourly_rate = request.form.get("hourly_rate")

        try:
            # Convert to float
            hours_worked = float(hours_worked)
            hourly_rate = float(hourly_rate)
            total_payment = round(hours_worked * hourly_rate, 2)

            # Update payroll
            it_payroll_collection.update_one(
                {"_id": payroll_id},
                {"$set": {
                    "hours_worked": hours_worked,
                    "hourly_rate": hourly_rate,
                    "total_payment": total_payment
                }}
            )

            flash("✅ Payroll updated successfully!", "success")
            return redirect(url_for("admin_payroll_bp.manage_it_payroll"))

        except ValueError:
            flash("❌ Invalid input! Please enter numeric values.", "danger")

    return render_template("admin/update_it_payroll.html", payroll_record=payroll_record)

@admin_payroll_bp.route('/create_it_payroll', methods=['GET', 'POST'])
@login_required
def create_it_payroll():
    """Allow Admin to create payroll for IT staff"""

    # Fetch all IT staff
    it_staff = list(it_collection.find({}, {"user_id": 1, "profile.name.first_name": 1, "profile.name.last_name": 1}))

    if request.method == 'POST':
        it_id = request.form.get("it_id")
        hours_worked = request.form.get("hours_worked")
        hourly_rate = request.form.get("hourly_rate")

        if not it_id or not hours_worked or not hourly_rate:
            flash("❌ All fields are required!", "danger")
            return redirect(url_for("admin_payroll_bp.create_it_payroll"))

        try:
            hours_worked = float(hours_worked)
            hourly_rate = float(hourly_rate)
            total_payment = round(hours_worked * hourly_rate, 2)

            payroll_data = {
                "it_id": it_id,
                "hours_worked": hours_worked,
                "hourly_rate": hourly_rate,
                "total_payment": total_payment
            }

            it_payroll_collection.insert_one(payroll_data)
            flash("✅ IT Payroll Created Successfully!", "success")
            return redirect(url_for("admin_payroll_bp.manage_it_payroll"))

        except ValueError:
            flash("❌ Invalid input! Please enter numeric values.", "danger")

    return render_template("admin/create_it_payroll.html", it_staff=it_staff)
@admin_payroll_bp.route('/manage_user_payroll', methods=['GET'])
@login_required
def manage_user_payroll():
    """Allow Admin to view and manage payroll records of Users"""

    user_payrolls = list(payroll_collection.find({}))

    # Fetch user names for display
    for payroll in user_payrolls:
        user = main_collection.find_one({"user_id": payroll["user_id"]}, {"profile.name.first_name": 1, "profile.name.last_name": 1})
        if user:
            payroll["user_name"] = f"{user.get('profile', {}).get('name', {}).get('first_name', '')} {user.get('profile', {}).get('name', {}).get('last_name', '')}".strip()
        else:
            payroll["user_name"] = "Unknown User"

    return render_template("admin/manage_user_payroll.html", user_payrolls=user_payrolls)


@admin_payroll_bp.route('/edit_user_payroll/<payroll_id>', methods=['GET', 'POST'])
@login_required
def edit_user_payroll(payroll_id):
    """Allow Admin to edit a User payroll record"""

    payroll = payroll_collection.find_one({"_id": ObjectId(payroll_id)})

    if not payroll:
        flash("❌ Payroll record not found!", "danger")
        return redirect(url_for("admin_payroll_bp.manage_user_payroll"))

    if request.method == 'POST':
        try:
            new_hours_worked = float(request.form.get("hours_worked"))
            new_hourly_rate = float(request.form.get("hourly_rate"))
            new_total_payment = round(new_hours_worked * new_hourly_rate, 2)

            payroll_collection.update_one(
                {"_id": ObjectId(payroll_id)},
                {"$set": {
                    "hours_worked": new_hours_worked,
                    "hourly_rate": new_hourly_rate,
                    "total_payment": new_total_payment
                }}
            )

            flash("✅ Payroll updated successfully!", "success")
            return redirect(url_for("admin_payroll_bp.manage_user_payroll"))

        except ValueError:
            flash("❌ Invalid input! Please enter numeric values.", "danger")

    return render_template("admin/edit_user_payroll.html", payroll=payroll)


@admin_payroll_bp.route('/delete_user_payroll/<payroll_id>', methods=['POST'])
@login_required
def delete_user_payroll(payroll_id):
    """Allow Admin to delete a User payroll record"""

    payroll = payroll_collection.find_one({"_id": ObjectId(payroll_id)})

    if not payroll:
        flash("❌ Payroll record not found!", "danger")
    else:
        payroll_collection.delete_one({"_id": ObjectId(payroll_id)})
        flash("✅ Payroll deleted successfully!", "success")

    return redirect(url_for("admin_payroll_bp.manage_user_payroll"))
