from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import boto3
import os
from bson import ObjectId
from dotenv import load_dotenv
from main_app.db_config import offboarding_files_collection, onboarding_files_collection, main_collection, it_collection, admin_collection
from utils.user_utils import get_all_users

# ✅ Load environment variables
load_dotenv()

# ✅ Separate AWS Configurations for Onboarding & Offboarding
AWS_S3_REGION = os.getenv("AWS_S3_REGION")

AWS_OFFBOARDING_BUCKET = os.getenv("AWS_OFFBOARDING_BUCKET")
AWS_OFFBOARDING_ACCESS_KEY = os.getenv("AWS_OFFBOARDING_ACCESS_KEY")
AWS_OFFBOARDING_SECRET_KEY = os.getenv("AWS_OFFBOARDING_SECRET_KEY")

AWS_ONBOARDING_BUCKET = os.getenv("AWS_ONBOARDING_BUCKET")
AWS_ONBOARDING_ACCESS_KEY = os.getenv("AWS_ONBOARDING_ACCESS_KEY")
AWS_ONBOARDING_SECRET_KEY = os.getenv("AWS_ONBOARDING_SECRET_KEY")

# ✅ Initialize separate S3 clients
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

# ✅ File Upload Blueprint
file_upload_bp = Blueprint("file_upload_bp", __name__)

def get_display_name(user_id):
    """Retrieve the display name for a user based on available profile data."""
    user_data = main_collection.find_one({"user_id": user_id}) or it_collection.find_one({"user_id": user_id}) or admin_collection.find_one({"user_id": user_id})

    if user_data:
        first_name = user_data.get("profile", {}).get("name", {}).get("first_name")
        last_name = user_data.get("profile", {}).get("name", {}).get("last_name")

        if first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name

    return user_id  # ❌ Fallback to User ID if no name found


# ✅ IT/Admin Uploads Offboarding Files for Users
@file_upload_bp.route('/upload_offboarding_file', methods=['GET', 'POST'])
@login_required
def upload_offboarding_file():
    """IT/Admin uploads offboarding files for users."""

    all_users = get_all_users()

    for user in all_users:
        user['display_name'] = get_display_name(user['user_id'])

    if request.method == 'POST':
        user_id = request.form.get("user_id", "").strip()
        file_type = request.form.get("file_type", "").strip()
        file = request.files.get("file")

        if not user_id or not file_type or not file:
            flash("❌ All fields are required!", "danger")
            return redirect(url_for("file_upload_bp.upload_offboarding_file"))

        s3_file_path = f"{file_type}/{user_id}/{file.filename}"

        try:
            # ✅ Upload to Offboarding Bucket
            s3_offboarding.upload_fileobj(file, AWS_OFFBOARDING_BUCKET, s3_file_path)

            # ✅ Generate S3 File URL
            file_url = f"https://{AWS_OFFBOARDING_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{s3_file_path}"

            # ✅ Save File Data in **offboarding_files_collection**
            offboarding_files_collection.insert_one({
                "user_id": user_id,
                "file_type": file_type,
                "file_name": file.filename,
                "s3_url": file_url,
                "uploaded_at": datetime.utcnow(),
                "process_type": "offboarding"
            })

            flash("✅ Offboarding file uploaded successfully!", "success")
            return redirect(url_for("file_upload_bp.upload_offboarding_file"))

        except Exception as e:
            flash(f"❌ File upload failed: {str(e)}", "danger")
            return redirect(url_for("file_upload_bp.upload_offboarding_file"))

    return render_template("main/upload_offboarding_file.html", users=all_users)


# ✅ Users Upload Onboarding Files
@file_upload_bp.route('/upload_onboarding_file', methods=['GET', 'POST'])
@login_required
def upload_onboarding_file():
    """User uploads onboarding files (e.g., personal documents, ID proofs, contracts)."""

    if request.method == 'POST':
        file_type = request.form.get("file_type", "").strip()
        file = request.files.get("file")

        if not file_type or not file:
            flash("❌ All fields are required!", "danger")
            return redirect(url_for("file_upload_bp.upload_onboarding_file"))

        user_id = current_user.user_id  # ✅ The logged-in user uploads their own files
        s3_file_path = f"{file_type}/{user_id}/{file.filename}"

        try:
            # ✅ Upload to Onboarding Bucket
            s3_onboarding.upload_fileobj(file, AWS_ONBOARDING_BUCKET, s3_file_path)

            # ✅ Generate S3 File URL
            file_url = f"https://{AWS_ONBOARDING_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{s3_file_path}"

            # ✅ Save File Data in **onboarding_files_collection**
            onboarding_files_collection.insert_one({
                "user_id": user_id,
                "file_type": file_type,
                "file_name": file.filename,
                "s3_url": file_url,
                "uploaded_at": datetime.utcnow(),
                "process_type": "onboarding"
            })

            flash("✅ Onboarding file uploaded successfully!", "success")
            return redirect(url_for("file_upload_bp.upload_onboarding_file"))

        except Exception as e:
            flash(f"❌ File upload failed: {str(e)}", "danger")
            return redirect(url_for("file_upload_bp.upload_onboarding_file"))

    return render_template("main/upload_onboarding_file.html")



# ✅ Users View Their Offboarding Files
@file_upload_bp.route('/view_offboarding_files', methods=['GET'])
@login_required
def view_offboarding_files():
    """Users can ONLY view the offboarding files uploaded for them"""
    files = list(offboarding_files_collection.find({"user_id": current_user.user_id}))
    return render_template("main/view_offboarding_files.html", files=files)

@file_upload_bp.route('/view_onboarding_files', methods=['GET'])
@login_required
def view_onboarding_files():
    """Allow users to view their own onboarding files."""
    files = list(onboarding_files_collection.find({"user_id": current_user.user_id}))
    return render_template("main/view_onboarding_files.html", files=files)


# ✅ IT/Admin View & Manage Offboarding Files
@file_upload_bp.route('/manage_files', methods=['GET'])
@login_required
def manage_files():
    """IT/Admin views & manages files uploaded for users."""
    
    all_users = get_all_users()
    for user in all_users:
        user['display_name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()

    selected_user_id = request.args.get("user_id", "").strip()
    files = []

    if selected_user_id:
        # ✅ Fetch files for the selected user from both collections
        offboarding_files = list(offboarding_files_collection.find({"user_id": selected_user_id}))
        onboarding_files = list(onboarding_files_collection.find({"user_id": selected_user_id}))

        # ✅ Combine file lists
        files = offboarding_files + onboarding_files

    return render_template("main/manage_files.html", users=all_users, files=files, selected_user_id=selected_user_id)
@file_upload_bp.route("/edit_file/<file_id>", methods=["GET", "POST"])
@login_required
def edit_file(file_id):
    """Edit file details including replacing the file"""
    
    file = offboarding_files_collection.find_one({"_id": ObjectId(file_id)})

    if not file:
        flash("❌ File not found or unauthorized!", "danger")
        return redirect(url_for("file_upload_bp.manage_offboarding_files"))

    if request.method == "POST":
        new_file_type = request.form.get("file_type")
        new_file_name = request.form.get("file_name")
        new_file = request.files.get("file")  # ✅ New file upload

        if not new_file_name:
            flash("❌ File name cannot be empty!", "danger")
            return redirect(url_for("file_upload_bp.edit_file", file_id=file_id))

        try:
            # ✅ Prepare new file path
            old_s3_key = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"
            new_s3_key = f"{new_file_type}/{file['user_id']}/{new_file_name}"

            if new_file:
                # ✅ Upload new file
                s3_offboarding.upload_fileobj(new_file, AWS_OFFBOARDING_BUCKET, new_s3_key)

                # ✅ Delete old file if it exists
                s3_offboarding.delete_object(Bucket=AWS_OFFBOARDING_BUCKET, Key=old_s3_key)

                # ✅ Update MongoDB with new file info
                offboarding_files_collection.update_one(
                    {"_id": ObjectId(file_id)},
                    {"$set": {
                        "file_type": new_file_type,
                        "file_name": new_file_name,
                        "s3_url": f"https://{AWS_OFFBOARDING_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{new_s3_key}",
                        "uploaded_at": datetime.utcnow(),
                    }}
                )

            else:
                # ✅ Just rename the file type & name in MongoDB
                offboarding_files_collection.update_one(
                    {"_id": ObjectId(file_id)},
                    {"$set": {
                        "file_type": new_file_type,
                        "file_name": new_file_name,
                    }}
                )

            flash("✅ File updated successfully!", "success")
            return redirect(url_for("file_upload_bp.manage_offboarding_files"))

        except Exception as e:
            flash(f"❌ File update failed: {str(e)}", "danger")

    return render_template("main/edit_file.html", file=file)



### **🔹 Delete File Route**
@file_upload_bp.route("/delete_file/<file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    """Delete a file from S3 and MongoDB."""

    file = offboarding_files_collection.find_one({"_id": ObjectId(file_id)})

    if not file:
        flash("❌ File not found!", "danger")
        return redirect(url_for("file_upload_bp.manage_offboarding_files"))

    file_name = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"

    try:
        s3_offboarding.delete_object(Bucket=AWS_OFFBOARDING_BUCKET, Key=file_name)
        offboarding_files_collection.delete_one({"_id": ObjectId(file_id)})

        flash("✅ File deleted successfully!", "success")

    except Exception as e:
        flash(f"❌ File deletion failed: {str(e)}", "danger")

    return redirect(url_for("file_upload_bp.manage_offboarding_files"))


@file_upload_bp.route('/manage_offboarding_files', methods=['GET'])
@login_required
def manage_offboarding_files():
    """Allow IT/Admin to view, edit, and delete the files they uploaded for users."""

    all_users = get_all_users()

    for user in all_users:
        user['display_name'] = get_display_name(user['user_id'])

    selected_user_id = request.args.get("user_id", "").strip()
    files = []

    if selected_user_id:
        files = list(offboarding_files_collection.find({"user_id": selected_user_id}))

    return render_template("main/manage_offboarding_files.html", users=all_users, files=files, selected_user_id=selected_user_id)


@file_upload_bp.route('/it_view_onboarding_files', methods=['GET'])
@login_required
def it_view_onboarding_files():
    """IT/Admin can view onboarding files uploaded by users."""
    
    if current_user.role != "IT" and current_user.role != "Admin":
        flash("❌ Unauthorized access!", "danger")
        return redirect(url_for("user_bp.dashboard"))

    all_users = get_all_users()

    for user in all_users:
        user['display_name'] = get_display_name(user['user_id'])

    selected_user_id = request.args.get("user_id", "").strip()
    files = []

    if selected_user_id:
        # ✅ Fetch files for the selected user from Onboarding Collection
        files = list(onboarding_files_collection.find({"user_id": selected_user_id}))

    return render_template("main/it_view_onboarding_files.html", users=all_users, files=files, selected_user_id=selected_user_id)


@file_upload_bp.route("/edit_user_onboarding_file/<file_id>", methods=["GET", "POST"])
@login_required
def edit_user_onboarding_file(file_id):
    """Allow users to edit their uploaded onboarding files."""

    file = onboarding_files_collection.find_one({"_id": ObjectId(file_id), "user_id": current_user.user_id})

    if not file:
        flash("❌ File not found or unauthorized!", "danger")
        return redirect(url_for("file_upload_bp.view_user_onboarding_files"))  # ✅ Fixed redirection

    if request.method == "POST":
        new_file_type = request.form.get("file_type")
        new_file_name = request.form.get("file_name")
        new_file = request.files.get("new_file")

        if not new_file_name:
            flash("❌ File name cannot be empty!", "danger")
            return redirect(url_for("file_upload_bp.edit_user_onboarding_file", file_id=file_id))

        try:
            old_s3_key = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"
            new_s3_key = f"{new_file_type}/{file['user_id']}/{new_file_name}"

            # ✅ If a new file is provided, replace the file in S3
            if new_file:
                s3_onboarding.delete_object(Bucket=AWS_ONBOARDING_BUCKET, Key=old_s3_key)
                s3_onboarding.upload_fileobj(new_file, AWS_ONBOARDING_BUCKET, new_s3_key)

            # ✅ Update MongoDB Record
            onboarding_files_collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {
                    "file_type": new_file_type,
                    "file_name": new_file_name,
                    "s3_url": f"https://{AWS_ONBOARDING_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{new_s3_key}"
                }}
            )

            flash("✅ File updated successfully!", "success")
            return redirect(url_for("file_upload_bp.view_user_onboarding_files"))  # ✅ Fixed redirection

        except Exception as e:
            flash(f"❌ File update failed: {str(e)}", "danger")

    return render_template("main/edit_user_onboarding_file.html", file=file)

@file_upload_bp.route('/view_user_onboarding_files', methods=['GET'])
@login_required
def view_user_onboarding_files():
    """Allow users to view their own uploaded onboarding files."""
    
    files = list(onboarding_files_collection.find({"user_id": current_user.user_id}))

    return render_template("main/view_onboarding_files.html", files=files)




@file_upload_bp.route("/delete_user_onboarding_file/<file_id>", methods=["POST"])
@login_required
def delete_user_onboarding_file(file_id):
    """Allow users to delete their own onboarding files."""

    file = onboarding_files_collection.find_one({"_id": ObjectId(file_id), "user_id": current_user.user_id})

    if not file:
        flash("❌ File not found or unauthorized!", "danger")
        return redirect(url_for("file_upload_bp.view_onboarding_files"))  # ✅ Fixed redirection

    try:
        s3_key = f"{file['file_type']}/{file['user_id']}/{file['file_name']}"
        s3_onboarding.delete_object(Bucket=AWS_ONBOARDING_BUCKET, Key=s3_key)

        onboarding_files_collection.delete_one({"_id": ObjectId(file_id)})

        flash("✅ File deleted successfully!", "success")
        return redirect(url_for("file_upload_bp.view_onboarding_files"))  # ✅ Fixed redirection

    except Exception as e:
        flash(f"❌ File deletion failed: {str(e)}", "danger")

    return redirect(url_for("file_upload_bp.view_onboarding_files"))  # ✅ Fixed redirection
