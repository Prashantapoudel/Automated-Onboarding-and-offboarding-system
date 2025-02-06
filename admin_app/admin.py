from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import AdminConfig
from admin_app import config
from flask_mail import Mail

# Initialize Flask App
admin_app = Flask(__name__)
admin_app.config.from_object(AdminConfig)
 

# Initialize MongoDB
mongo = PyMongo(admin_app)
db_admin = mongo.db  # This now connects to 'Admin' DB


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(admin_app)
login_manager.login_view = "admin_routes.login"

# Import Routes
from admin_app.routes.admin_routes import admin_bp

app = Flask(__name__)
app.config.from_object(config)
mail = Mail(app)

#Register Blueprints

admin_app.register_blueprint(admin_bp)


@admin_app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
if __name__ == "__main__":
    admin_app.run(port=5001, debug=True)



