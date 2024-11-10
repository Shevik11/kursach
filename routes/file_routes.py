from flask import Blueprint, request
from flask_login import login_required
from app import app
from main import FileWatcher
from routes.functions_file import upload_file, save_file, delete_file, edit_file, list_files
file_bp = Blueprint("files", __name__)

checker = FileWatcher("./uploads", [".txt", ".doc", ".docx", ".pdf"])


@app.route("/", methods=["GET", "POST"])
@login_required
def list():
    action = request.args.get("action")
    filename = request.args.get("filename")

    match (request.method, action):
        case ("POST", _) if "file" in request.files:
            return upload_file()
        case ("POST", _) if "content" in request.form and "filename" in request.form:
            return save_file()
        case (_, "delete") if filename:
            return delete_file(filename)
        case (_, "edit") if filename:
            return edit_file(filename)
        case _:
            return list_files()