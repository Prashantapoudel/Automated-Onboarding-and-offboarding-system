from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve MongoDB URI from environment variable
MONGO_URI = os.getenv("mongodb+srv://prashantapoudel:Prashantapdl2003@hiresync.fzebe.mongodb.net/")

def get_mongo_connection():
    """
    Establish MongoDB connection and return the client.
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client["Employment_Management"]  # Your main database name
        return db
    except Exception as e:
        print(f"❌ MongoDB Connection Error: {e}")
        return None
