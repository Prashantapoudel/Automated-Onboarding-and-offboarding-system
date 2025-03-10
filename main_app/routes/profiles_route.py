from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from main_app.db_config import main_collection, it_collection

# ✅ Unified Blueprint for Profile Management
profile_bp = Blueprint("profile_bp", __name__)

def get_user_collection(user_id):
    """Helper function to get the correct collection"""
    if user_id.startswith("U"):
        return main_collection, "User"
    elif user_id.startswith("IT"):
        return it_collection, "IT"
    return None, None

@profile_bp.route('/profile', methods=['GET'])
@login_required
def view_profile():
    """View Profile Page for IT and User"""
    user_id = current_user.user_id
    collection, role = get_user_collection(user_id)
    user_data = collection.find_one({"user_id": user_id})
    # ✅ Debugging
    print(f"🛠 DEBUG: Retrieved User Data: {user_data}")

    # ✅ Check if profile exists
    profile_exists = "profile" in user_data

    # ✅ Redirect to create profile if not exists
    if not profile_exists:
        flash("You don't have a profile yet. Please create one.")
        return redirect(url_for('profile_bp.create_profile'))

    return render_template('Main/profile.html', user=user_data, role=role)

@profile_bp.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    """Create Profile Page"""
    user_id = current_user.user_id
    collection, role = get_user_collection(user_id)

    if request.method == 'POST':
        # Get the profile data from form
        profile_data = {
            "addresses": {
                "home": request.form.get("home_address"),
                "mailing": request.form.get("mailing_address")
            },
            "contact_details": {
                "phone": request.form.get("phone"),
                "email": request.form.get("email")
            },
            "name": {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name")
            },
            "emergency_contacts": {
                "contact_name": request.form.get("emergency_contact_name"),
                "contact_phone": request.form.get("emergency_contact_phone")
            },
            "additional_information": request.form.get("additional_information")
        }

        # ✅ Create the profile in MongoDB
        collection.update_one({"user_id": user_id}, {"$set": {"profile": profile_data}})
        flash("Profile created successfully!", "success")
        return redirect(url_for('profile_bp.view_profile'))

    return render_template('Main/create_profile.html', role=role)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit Profile Page"""
    user_id = current_user.user_id
    collection, role = get_user_collection(user_id)
    user_data = collection.find_one({"user_id": user_id})

    if request.method == 'POST':
        # Get the updated profile data from form
        profile_data = {
            "addresses": {
                "home": request.form.get("home_address"),
                "mailing": request.form.get("mailing_address")
            },
            "contact_details": {
                "phone": request.form.get("phone"),
                "email": request.form.get("email")
            },
            "name": {
                "first_name": request.form.get("first_name"),
                "last_name": request.form.get("last_name")
            },
            "emergency_contacts": {
                "contact_name": request.form.get("emergency_contact_name"),
                "contact_phone": request.form.get("emergency_contact_phone")
            },
            "additional_information": request.form.get("additional_information")
        }

        # ✅ Update the profile in MongoDB
        collection.update_one({"user_id": user_id}, {"$set": {"profile": profile_data}})
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile_bp.view_profile'))

    return render_template('Main/edit_profile.html', user=user_data, role=role)
