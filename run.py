import os
import sys
from src.app.app import app

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Live reload in dev mode
    if os.environ.get("FLASK_ENV") == "development":
        from livereload import Server
        server = Server(app.wsgi_app)
        server.serve(port=5000, host="localhost")
    else:
        app.run(debug=True)
