from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import AdminConfig

# Initialize Flask App
admin_app = Flask(__name__)
admin_app.config.from_object(AdminConfig)

# Initialize MongoDB
mongo = PyMongo(admin_app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(admin_app)
login_manager.login_view = "admin_routes.login"

# Import Routes
from routes import admin_routes

# Register Blueprints
admin_app.register_blueprint(admin_routes.admin_bp, url_prefix="/admin")

if __name__ == "__main__":
    admin_app.run(port=5001, debug=True)
