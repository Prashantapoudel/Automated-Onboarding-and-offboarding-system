#admin smtp server
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("EMAIL_USER")  # ✅ Use environment variable
    MAIL_PASSWORD = os.getenv("EMAIL_PASS")  # ✅ Use environment variable
