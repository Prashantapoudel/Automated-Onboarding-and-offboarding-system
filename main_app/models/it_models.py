from flask_login import UserMixin
from main_app.db_config import it_collection

class ITModel(UserMixin):
    def __init__(self, user_id, email, role):
        self.id = user_id 
        self.user_id = user_id 
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        """Retrieve user from IT collection"""
        user_data = it_collection.find_one({"user_id": user_id})
        if user_data:
            return ITModel(
                user_id=user_data["user_id"],
                email=user_data.get("email", ""),
                role=user_data.get("role", "IT")
            )
        return None  # IT User not found
