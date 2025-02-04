import pymongo
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB URIs from .env
mongo_main_uri = os.getenv("MONGO_URI_MAIN")
mongo_admin_uri = os.getenv("MONGO_URI_ADMIN")

try:
    # Test connection for Main DB
    client_main = pymongo.MongoClient(mongo_main_uri)
    db_main = client_main["Main"]
    print("✅ Connected successfully to Main DB!")
    print("📂 Collections in Main:", db_main.list_collection_names())

    # Test connection for Admin DB
    client_admin = pymongo.MongoClient(mongo_admin_uri)
    db_admin = client_admin["Admin"]
    print("✅ Connected successfully to Admin DB!")
    print("📂 Collections in Admin:", db_admin.list_collection_names())

except Exception as e:
    print("❌ Connection Failed:", e)
