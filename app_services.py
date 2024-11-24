from flask import Flask, send_from_directory
from extensions import mail
from auth.auth_routes import auth_blueprint
from dashboard.dashboard_routes import dashboard_blueprint
import os
from extensions import mail, UPLOAD_FOLDER
from flask_mail import Message


def configure_app(app):
    app.config.from_object("config.Config")
    app.secret_key = app.config["SECRET_KEY"]


def initialize_extensions(app):
    mail.init_app(app)


def register_blueprints(app):
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(dashboard_blueprint, url_prefix="/dashboard")
    # app.register_blueprint(edit_blueprint, url_prefix="/edit")


def register_routes(app):
    @app.route("/uploads/<username>/<filename>")
    def uploaded_file(username, filename):
        return send_from_directory(os.path.join(UPLOAD_FOLDER, username), filename)

    @app.route("/test_email")
    def test_email():
        try:
            msg = Message(
                "Test Email from Flask-Mail", recipients=["maksym.shevchuk@lnu.edu.ua"]
            )  # Замініть на вашу пошту
            msg.body = "This is a test email to verify SMTP configuration."
            mail.send(msg)
            return "Test email sent successfully!"
        except Exception as e:
            return f"Failed to send email: {e}"
