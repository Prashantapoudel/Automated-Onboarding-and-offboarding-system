from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import boto3
import os
from bson import ObjectId
from dotenv import load_dotenv
from main_app.db_config import onboarding_files_collection, offboarding_files_collection, main_collection, it_collection, admin_collection
from utils.user_utils import get_all_users

# ✅ Load environment variables
load_dotenv()

# ✅ AWS Configurations
AWS_S3_REGION = os.getenv("AWS_S3_REGION")

AWS_OFFBOARDING_BUCKET = os.getenv("AWS_OFFBOARDING_BUCKET")
AWS_OFFBOARDING_ACCESS_KEY = os.getenv("AWS_OFFBOARDING_ACCESS_KEY")
AWS_OFFBOARDING_SECRET_KEY = os.getenv("AWS_OFFBOARDING_SECRET_KEY")

AWS_ONBOARDING_BUCKET = os.getenv("AWS_ONBOARDING_BUCKET")
AWS_ONBOARDING_ACCESS_KEY = os.getenv("AWS_ONBOARDING_ACCESS_KEY")
AWS_ONBOARDING_SECRET_KEY = os.getenv("AWS_ONBOARDING_SECRET_KEY")

# ✅ Initialize S3 clients
s3_offboarding = boto3.client(
    "s3",
    aws_access_key_id=AWS_OFFBOARDING_ACCESS_KEY,
    aws_secret_access_key=AWS_OFFBOARDING_SECRET_KEY,
    region_name=AWS_S3_REGION
)

s3_onboarding = boto3.client(
    "s3",
    aws_access_key_id=AWS_ONBOARDING_ACCESS_KEY,
    aws_secret_access_key=AWS_ONBOARDING_SECRET_KEY,
    region_name=AWS_S3_REGION
)

file_bp = Blueprint("file_bp", __name__)
def get_all_users():
    """Retrieve all users with their names and emails."""
    users = list(main_collection.find({}, {"user_id": 1, "profile.name.first_name": 1, "profile.name.last_name": 1}))

    for user in users:
        profile = user.get("profile", {}).get("name", {})
        first_name = profile.get("first_name", "Unknown")
        last_name = profile.get("last_name", "")
        user["display_name"] = f"{first_name} {last_name}".strip()  # ✅ Properly format name

        if user["display_name"] == "Unknown":
            user["display_name"] = user["user_id"]  # Fallback to user_id if no name found

    print(f"🔍 DEBUG: Processed {len(users)} users.")  # ✅ Debugging Log

    return users


def get_display_name(user_id):
    """Retrieve the display name for a user based on available profile data."""
    if not user_id:
        return "Unknown User"

    user_data = (
        main_collection.find_one({"user_id": user_id}) or
        it_collection.find_one({"user_id": user_id}) or
        admin_collection.find_one({"user_id": user_id})
    )

    if user_data:
        first_name = user_data.get("profile", {}).get("name", {}).get("first_name", "Unknown")
        last_name = user_data.get("profile", {}).get("name", {}).get("last_name", "")
        return f"{first_name} {last_name}".strip()

    return "Unknown User"   # ❌ Fallback to "Unknown User" if no name found
### **🔹 View Onboarding Files (User)**
@file_bp.route('/admin_view_user_onboarding_files', methods=['GET'])
@login_required
def admin_view_user_onboarding_files():
    """Allow admins to view and manage onboarding files uploaded by users."""
    
    all_users = get_all_users()  # Fetch all users
    selected_user_id = request.args.get("user_id", "").strip()

    files = []
    
    if selected_user_id:
        files = list(onboarding_files_collection.find({"user_id": selected_user_id}))

    return render_template(
        "admin/view_user_onboarding_files.html",
        users=all_users,
        files=files,
        selected_user_id=selected_user_id
    )


### **🔹 View Offboarding Files (IT/Admin)**
@file_bp.route('/view_offboarding_files', methods=['GET'])
@login_required
def view_offboarding_files():
    """Admins should be able to view ALL offboarding files, while users see only their own."""

    try:
        user_id = current_user.user_id  # This will fail for Admins
    except AttributeError:
        user_id = None  # Admin has no user_id

    # ✅ If Admin, fetch ALL offboarding files
    if user_id is None:  
        print("🔍 DEBUG: Admin is viewing all offboarding files.")
        files = list(offboarding_files_collection.find({}))  # Admin sees all files
    else:
        print(f"🔍 DEBUG: User is viewing their own offboarding files. User ID -> {user_id}")
        files = list(offboarding_files_collection.find({"user_id": user_id}))  # Users see their own files

    # ✅ Add uploader and receiver details for each file
    for file in files:
        uploader = get_display_name(file.get("uploaded_by", "Unknown"))  # Fetch who uploaded
        receiver = get_display_name(file.get("user_id", "Unknown"))  # Fetch who it's for

        file["uploaded_by_name"] = uploader
        file["uploaded_for_name"] = receiver

    return render_template("admin/view_offboarding_files.html", files=files, get_display_name=get_display_name)


### **🔹 Edit Onboarding File (User)**
@file_bp.route("/edit_offboarding_file/<file_id>", methods=["GET", "POST"])
@login_required
def edit_offboarding_file(file_id):
    """Allow Admin/IT to edit offboarding files."""
    
    file = offboarding_files_collection.find_one({"_id": ObjectId(file_id)})

    if not file:
        flash("❌ File not found!", "danger")
        return redirect(url_for("file_bp.view_offboarding_files"))

    if request.method == "POST":
        new_file_type = request.form.get("file_type")
        new_file_name = request.form.get("file_name")
        new_file = request.files.get("file")

        if not new_file_name:
            flash("❌ File name cannot be empty!", "danger")
            return redirect(url_for("file_bp.edit_offboarding_file", file_id=file_id))

        try:
            old_s3_key = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"
            new_s3_key = f"{new_file_type}/{file['user_id']}/{new_file_name}"

            if new_file:
                # ✅ Upload new file & delete old file
                s3_offboarding.upload_fileobj(new_file, AWS_OFFBOARDING_BUCKET, new_s3_key)
                s3_offboarding.delete_object(Bucket=AWS_OFFBOARDING_BUCKET, Key=old_s3_key)

            # ✅ Update MongoDB Record
            offboarding_files_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {
                    "file_type": new_file_type,
                    "file_name": new_file_name,
                    "s3_url": f"https://{AWS_OFFBOARDING_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{new_s3_key}",
                    "uploaded_at": datetime.utcnow(),
                }}
            )

            flash("✅ File updated successfully!", "success")
            return redirect(url_for("file_bp.view_offboarding_files"))

        except Exception as e:
            flash(f"❌ File update failed: {str(e)}", "danger")

    return render_template("admin/edit_offboarding_file.html", file=file)

### **🔹 Delete Onboarding File (User)**
@file_bp.route("/delete_user_onboarding_file/<file_id>", methods=["POST"])
@login_required
def delete_user_onboarding_file(file_id):
    """Allow users to delete their own onboarding files."""

    file = onboarding_files_collection.find_one({"_id": ObjectId(file_id), "user_id": current_user.user_id})

    if not file:
        flash("❌ File not found or unauthorized!", "danger")
        return redirect(url_for("file_bp.view_onboarding_files"))

    try:
        s3_key = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"
        s3_onboarding.delete_object(Bucket=AWS_ONBOARDING_BUCKET, Key=s3_key)

        onboarding_files_collection.delete_one({"_id": ObjectId(file_id)})

        flash("✅ File deleted successfully!", "success")
        return redirect(url_for("file_bp.view_onboarding_files"))

    except Exception as e:
        flash(f"❌ File deletion failed: {str(e)}", "danger")

    return redirect(url_for("file_bp.view_onboarding_files"))


### **🔹 Delete Offboarding File (IT/Admin)**
@file_bp.route("/delete_offboarding_file/<file_id>", methods=["POST"])
@login_required
def delete_offboarding_file(file_id):
    """Allow IT/Admin to delete offboarding files for users."""

    file = offboarding_files_collection.find_one({"_id": ObjectId(file_id)})

    if not file:
        flash("❌ File not found!", "danger")
        return redirect(url_for("file_bp.view_offboarding_files"))

    try:
        s3_key = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"
        s3_offboarding.delete_object(Bucket=AWS_OFFBOARDING_BUCKET, Key=s3_key)

        offboarding_files_collection.delete_one({"_id": ObjectId(file_id)})

        flash("✅ File deleted successfully!", "success")
        return redirect(url_for("file_bp.view_offboarding_files"))

    except Exception as e:
        flash(f"❌ File deletion failed: {str(e)}", "danger")

    return redirect(url_for("file_bp.view_offboarding_files"))
