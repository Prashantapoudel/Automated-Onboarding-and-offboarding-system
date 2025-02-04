import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MainConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI_MAIN")  # Connects to 'Main' Database

class AdminConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI_ADMIN")  # Connects to 'Admin' Database
