from app import app
from routes.auth_routes import auth_bp
from routes.file_routes import file_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(file_bp, url_prefix="/files")

if __name__ == "__main__":
    app.run(debug=True)
