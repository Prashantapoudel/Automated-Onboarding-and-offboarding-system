import pymongo
from main_app.db_config import main_collection, it_collection, admin_collection

def get_all_users():
    """Retrieve all Users, IT, and Admins from the database for both apps."""
    
    users = list(main_collection.find({}, {"user_id": 1, "email": 1, "role": 1, "_id": 0}))
    it_users = list(it_collection.find({}, {"user_id": 1, "email": 1, "role": 1, "_id": 0}))
    admins = list(admin_collection.find({}, {"user_id": 1, "email": 1, "role": 1, "_id": 0}))

    all_users = users + it_users + admins  # ✅ Combine all roles into a single list
    
    return all_users  # ✅ Return structured list of users
