from flask import Flask
from flask_mail import Mail
from admin_app.config import Config  # If inside a submodule


# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)  # ✅ Load configuration

# Initialize Flask-Mail
mail = Mail(app)  #