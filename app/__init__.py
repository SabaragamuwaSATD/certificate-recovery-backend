from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Initialize Firebase (already handled in firebase.py)
    from app.services import firebase
    firebase  # Imported for initialization

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.certificates import cert_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cert_bp, url_prefix='/api/certificates')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    return app