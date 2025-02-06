#admin smtp server
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Secret Key for Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")

