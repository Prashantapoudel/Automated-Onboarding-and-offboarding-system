from main_app.main_app import main_app  # Explicitly import from main_app
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    main_app.run(host="0.0.0.0", port=port, debug=True)
