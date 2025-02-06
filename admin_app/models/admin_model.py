from flask_login import UserMixin

class AdminUser(UserMixin):
 class AdminUser(UserMixin):
    def __init__(self, user_id, email):  # ✅ Default to "superuser"
        self.id = user_id 
        self.email = email
        
    def get_id(self):
        return str(self.id) 
