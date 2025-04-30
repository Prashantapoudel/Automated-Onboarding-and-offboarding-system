from admin_app.admin import admin_app
import os 

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))  # fallback to 5000 if PORT not set
    admin_app.run(host="0.0.0.0", port=port, debug=True)
