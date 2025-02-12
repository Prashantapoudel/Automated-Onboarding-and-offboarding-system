import os

class Config:
    """Configuration settings for Flask app"""
    
    # ✅ Secret Key for Flask Sessions & Token Generation
    SECRET_KEY = os.getenv("SECRET_KEY")  # Use env variables in production
    
    # ✅ Flask-Mail Configuration (Change to your email provider)
    MAIL_SERVER = 'smtp.gmail.com'  # Use SMTP server (Gmail, Outlook, etc.)
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("EMAIL_USER")  # Store in env variable
    MAIL_PASSWORD = os.getenv("EMAIL_PASS")  # Store securely in env variable
    MAIL_DEFAULT_SENDER = MAIL_USERNAME  # Default sender email
    
    # ✅ MongoDB URI (Modify for Production)
    MONGO_URI = os.getenv("MONGO_URI")
