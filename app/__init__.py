from flask import Flask, send_from_directory
from flask_cors import CORS  # Import CORS
from flask_swagger_ui import get_swaggerui_blueprint
import os

def create_app():
    app = Flask(__name__, static_folder="static")
    app.config.from_object('app.config.Config')

    # Enable CORS for the entire app (or specify origins as needed)
    CORS(app)

    # Initialize Firebase (already handled in firebase.py)
    from app.services import firebase
    firebase  # Imported for initialization

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.certificates import cert_bp
    from app.routes.admin import admin_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cert_bp, url_prefix='/api/certificates')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(profile_bp, url_prefix='/api/profile')

    # Swagger UI setup
    SWAGGER_URL = "/api/docs"
    API_URL = "/static/swagger.yaml"  # Correct path for static file

    swagger_bp = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={"app_name": "Certificate API"}
    )
    app.register_blueprint(swagger_bp, url_prefix=SWAGGER_URL)

    # Add route to serve static files manually
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)

    return app
