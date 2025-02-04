import pymongo
import uuid
from werkzeug.security import generate_password_hash

# Connect to MongoDB (Admin DB)
mongo_uri = "mongodb+srv://prashantapoudel:Prashantapdl2003@hiresync.fzebe.mongodb.net/Admin?retryWrites=true&w=majority"
client = pymongo.MongoClient(mongo_uri)
db = client["Employment_Management"]  # ✅ Make sure this matches exactly!
admin_collection = db["Admin"]  # ✅ Use the correct collection name

# Create an Admin user
admin_user = {
    "_id": str(uuid.uuid4()),  # Unique Admin ID
    "username": "SuperAdmin",
    "email": "admin@hiresync.com",
    "password": generate_password_hash("admin123"),  # Hashed password using Werkzeug
    "role": "Admin"
}

# Insert into MongoDB
admin_collection.insert_one(admin_user)
print(f"✅ Admin user created!\nEmail: {admin_user['email']}\nPassword: admin123 (Change this later)")
