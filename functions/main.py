from firebase_functions import https_fn
from firebase_admin import initialize_app
import sys
import os

# Important: ensure the submodules (src, config) can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

initialize_app()

# Import the FastAPI application
from src.api.main import app
from a2wsgi import ASGIMiddleware

# Convert FastAPI's ASGI interface to WSGI since Firebase Python Gen 2 uses WSGI/Flask internally
wsgi_app = ASGIMiddleware(app)

@https_fn.on_request(timeout_sec=60, memory=512, max_instances=10)
def api(req: https_fn.Request) -> https_fn.Response:
    # Use Werkzeug's from_app to bridge the WSGI app and the Flask Request environ
    return https_fn.Response.from_app(wsgi_app, req.environ)