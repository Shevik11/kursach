from flask import Flask
from extensions import mail
from blueprints.auth import auth_blueprint
from blueprints.dashboard import dashboard_blueprint
from blueprints.edit import edit_blueprint
import os
from flask import send_from_directory
from blueprints.dashboard import UPLOAD_FOLDER
from flask_mail import Mail, Message

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.secret_key = app.config['SECRET_KEY']
    # Ініціалізація розширень
    mail.init_app(app)

    @app.route('/uploads/<username>/<filename>')
    def uploaded_file(username, filename):
        return send_from_directory(os.path.join(UPLOAD_FOLDER, username), filename)

    @app.route('/test_email')
    def test_email():
        try:
            msg = Message("Test Email from Flask-Mail",
                          recipients=["maksym.shevchuk@lnu.edu.ua"])  # Замініть на вашу пошту
            msg.body = "This is a test email to verify SMTP configuration."
            mail.send(msg)
            return "Test email sent successfully!"
        except Exception as e:
            return f"Failed to send email: {e}"

    # Реєстрація blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(dashboard_blueprint, url_prefix='/dashboard')
    app.register_blueprint(edit_blueprint, url_prefix='/edit')


    return app

if __name__ == '__main__':
    app = create_app()
    app.config["MAIL_DEBUG"] = True
    app.run(debug=True)
