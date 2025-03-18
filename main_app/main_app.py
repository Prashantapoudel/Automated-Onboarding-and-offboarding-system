from flask import Flask, render_template, redirect , session, url_for
from flask_pymongo import PyMongo
from flask_login import LoginManager
from config import MainConfig
from main_app.models.user_models import UserModel
from main_app.models.it_models import ITModel
from main_app.config import Config
from flask_mail import Mail
import redis
from flask import Flask, session
from flask_session import Session

app = Flask(__name__)

# Initialize Flask App
main_app = Flask(__name__,)
main_app.config.from_object(MainConfig)

main_app.config.from_object(Config)  # ✅ Load email config
mail = Mail(main_app) 

# Initialize MongoDB
mongo = PyMongo(main_app)
db_main = mongo.db  # This now connects to 'Main' DB


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.init_app(app)
login_manager.init_app(main_app)
login_manager.login_view = "user_routes.login"
@login_manager.user_loader
def load_user(user_id):
    """Fetch user from MAIN or IT collection"""
    user = UserModel.get(user_id) or ITModel.get(user_id)  # ✅ Try MAIN first, then IT
    return user

# Import Routes
from main_app.routes import user_routes, it_routes 
from main_app.routes.it_routes import it_bp
from main_app.routes.user_routes import user_bp
from main_app.routes.login_routes import login_bp  # ✅ Import login blueprint
from main_app.routes.change_password_routes import change_password_bp
from main_app.routes.reset_password_routes import reset_password_bp  
from main_app.routes.profiles_route import profile_bp  # ✅ Import Unified Profile Routes
from main_app.routes.it_create_user import it_create_user_bp  # ✅ Import IT Create User Route
from main_app.routes.messaging_routes import messaging_bp  # ✅ Import messaging blueprint
from main_app.routes.file_upload import file_upload_bp  # ✅ Import file upload blueprint

main_app.register_blueprint(user_bp)
main_app.register_blueprint(it_bp)
main_app.register_blueprint(login_bp)  # ✅ Register login routes
main_app.register_blueprint(change_password_bp) 
main_app.register_blueprint(reset_password_bp)
main_app.register_blueprint(profile_bp)
main_app.register_blueprint(it_create_user_bp) 
main_app.register_blueprint(messaging_bp)
main_app.register_blueprint(file_upload_bp)
@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to the login page"""
    return redirect(url_for('login_bp.login'))

@main_app.after_request
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
     main_app.run(port=5000, debug=True)  
