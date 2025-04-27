from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from main_app.db_config import main_collection, it_collection
from bson import ObjectId

profile_bp = Blueprint("profile_bp", __name__)  # ✅ Blueprint for profile management

def get_display_name(user):
    """Extracts full name from user profile or returns User ID."""
    if user:
        first_name = user.get("profile", {}).get("name", {}).get("first_name", "")
        last_name = user.get("profile", {}).get("name", {}).get("last_name", "")
        return f"{first_name} {last_name}".strip() or user.get("user_id")
    return "Unknown User"

@profile_bp.route("/profiles")
@login_required
def list_profiles():
    """Admin can view all user & IT profiles."""
    users = list(main_collection.find({}))  # Fetch all users
    it_users = list(it_collection.find({}))  # Fetch all IT users

    for user in users + it_users:
        user["display_name"] = get_display_name(user)

    return render_template("admin/list_profiles.html", users=users, it_users=it_users)

@profile_bp.route("/profiles/<user_id>")
@login_required
def view_profile(user_id):
    """View a specific user's profile."""
    user = main_collection.find_one({"user_id": user_id}) or it_collection.find_one({"user_id": user_id})

    if not user:
        flash("❌ User profile not found!", "danger")
        return redirect(url_for("profile_bp.list_profiles"))

    return render_template("admin/view_profile.html", user=user)

@profile_bp.route("/edit/<user_id>", methods=["GET", "POST"])
@login_required
def edit_profile(user_id):
    """Admin edits user profile details."""
    user = main_collection.find_one({"user_id": user_id}) or it_collection.find_one({"user_id": user_id})

    if not user:
        flash("❌ User not found!", "danger")
        return redirect(url_for("profile_bp.list_profiles"))

    if request.method == "POST":
        # ✅ Get updated values
        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        email = request.form.get("email").strip()

        # ✅ Update MongoDB
        collection = main_collection if "role" in user and user["role"] == "USER" else it_collection
        collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "profile.name.first_name": first_name,
                "profile.name.last_name": last_name,
                "email": email
            }}
        )

        flash("✅ Profile updated successfully!", "success")
        return redirect(url_for("profile_bp.view_profile", user_id=user_id))

    return render_template("admin/edit_profile.html", user=user)

@profile_bp.route("/delete/<user_id>", methods=["POST"])
@login_required
def delete_profile(user_id):
    """Admin deletes a user profile."""
    result = main_collection.delete_one({"user_id": user_id})
    result_it = it_collection.delete_one({"user_id": user_id})

    if result.deleted_count or result_it.deleted_count:
        flash("🗑️ Profile deleted successfully!", "info")
    else:
        flash("❌ Profile not found!", "danger")

    return redirect(url_for("profile_bp.list_profiles"))
