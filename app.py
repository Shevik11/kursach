from flask import Flask
from app_services import (
    configure_app,
    initialize_extensions,
    register_blueprints,
    register_routes,
)


def create_app():
    app = Flask(__name__)
    configure_app(app)
    initialize_extensions(app)
    register_blueprints(app)
    register_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.config["MAIL_DEBUG"] = True
    app.run(host="0.0.0.0", port=5000, debug=True)
