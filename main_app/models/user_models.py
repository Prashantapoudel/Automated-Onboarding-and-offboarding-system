from flask_login import UserMixin
from main_app.db_config import main_collection

class UserModel(UserMixin):
    def __init__(self, user_id, email, role):
        self.id = user_id  # ✅ User ID stored in `id`
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        """Retrieve user from MAIN collection"""
        user_data = main_collection.find_one({"user_id": user_id})
        if user_data:
            return UserModel(
                user_id=user_data["user_id"],
                email=user_data.get("email", ""),
                role=user_data.get("role", "MAIN")
            )
        return None  # User not found
