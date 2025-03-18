from flask_login import UserMixin
from main_app.db_config import admin_collection

class AdminUser(UserMixin):
    def __init__(self, user_id, email, role="Admin"):
        self.id = user_id  # ✅ Flask-Login uses `id`
        self.user_id = user_id  # ✅ Add `user_id` explicitly
        self.email = email
        self.role = role  # Default role: Admin

    @staticmethod
    def get(user_id):
        """Retrieve admin user from Admin collection"""
        admin_data = admin_collection.find_one({"user_id": user_id})
        if admin_data:
            return AdminUser(
                user_id=admin_data["user_id"],
                email=admin_data.get("email", ""),
                role=admin_data.get("role", "Admin")
            )
        return None
