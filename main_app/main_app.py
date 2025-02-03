from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import MainConfig

# Initialize Flask App
main_app = Flask(__name__)
main_app.config.from_object(MainConfig)

# Initialize MongoDB
mongo = PyMongo(main_app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(main_app)
login_manager.login_view = "user_routes.login"

# Import Routes
from routes import user_routes, it_routes

# Register Blueprints
main_app.register_blueprint(user_routes.user_bp, url_prefix="/user")
main_app.register_blueprint(it_routes.it_bp, url_prefix="/it")

if __name__ == "__main__":
    main_app.run(port=5000, debug=True)
