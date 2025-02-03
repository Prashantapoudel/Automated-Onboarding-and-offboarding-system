import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MainConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")  # Flask session security
    MONGO_URI = os.getenv("MONGO_URI_MAIN")

class AdminConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI_ADMIN")
