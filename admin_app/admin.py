from flask import Flask, render_template
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import AdminConfig
from admin_app import config
from flask_mail import Mail
from flask import Flask, session
from flask_session import Session
app = Flask(__name__)
import redis

# Initialize Flask App
admin_app = Flask(__name__)
admin_app.config.from_object(AdminConfig)
 

# Initialize MongoDB
mongo = PyMongo(admin_app)
db_admin = mongo.db  


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.init_app(app)
login_manager.init_app(admin_app)
login_manager.login_view = "admin_routes.login"

# Import Routes
from admin_app.routes.admin_routes import admin_bp
# from admin_app.routes.admin_messaging import admin_messaging_bp
from admin_app.routes.admin_messaging import messaging_bp
from admin_app.routes.profiles import profile_bp
from admin_app.routes.file_management import file_bp
from admin_app.routes.admin_create_it import admin_create_it_bp
from admin_app.routes.it_payroll import admin_payroll_bp
from admin_app.routes.task_route import task_bp

app.config.from_object(config)
mail = Mail(app)

#Register Blueprints

admin_app.register_blueprint(admin_bp)
admin_app.register_blueprint(messaging_bp)
admin_app.register_blueprint(profile_bp)  
admin_app.register_blueprint(file_bp)
admin_app.register_blueprint(admin_create_it_bp)
admin_app.register_blueprint(admin_payroll_bp)
admin_app.register_blueprint(task_bp)





@admin_app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True  # Optional for security
app.config["SESSION_KEY_PREFIX"] = "hiresync_"  # Namespace
app.config["SESSION_REDIS"] = redis.Redis(host="localhost", port=6379)

# ✅ Initialize the Session
Session(app)
if __name__ == "__main__":
    admin_app.run(port=5001, debug=True)



