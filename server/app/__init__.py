from flask import Flask, send_from_directory
from flask_cors import CORS

from .routes import api_bp, page_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    CORS(app)

    app.register_blueprint(page_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/static/<path:filename>")
    def static_files(filename: str):
        return send_from_directory(app.static_folder, filename)

    return app
