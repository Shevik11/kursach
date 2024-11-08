from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import app
from utils import read_file_content, save_file_content
from datetime import datetime
from main import FileWatcher


file_bp = Blueprint("files", __name__)

checker = FileWatcher("./uploads", [".txt", ".doc", ".docx", ".pdf"])


@app.route("/", methods=["GET", "POST"])
@login_required
def list():
    action = request.args.get("action")
    filename = request.args.get("filename")

    # Завантаження нового файлу
    if request.method == "POST" and "file" in request.files:
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            flash(f"Файл {filename} успішно завантажено", "success")
            return redirect(url_for("list"))

    # Збереження відредагованого файлу
    elif (
        request.method == "POST"
        and "content" in request.form
        and "filename" in request.form
    ):
        filename = request.form["filename"]
        content = request.form["content"]
        description = request.form["description"]  # Get the user-provided description

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
        if os.path.exists(file_path):
            if save_file_content(file_path, content):
                current_states = checker._get_directory_state()
                changes = checker._detect_change_type(
                    checker.last_states, current_states
                )
                for file_path, change_type, size in changes:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user = current_user.username
                    if change_type:
                        change_record = {
                            "file": str(file_path).split("\\")[-1],
                            "type": change_type,
                            "time": timestamp,
                            "user": user,
                            "description": description,  # Add the description to the log
                        }
                        if size is not None:
                            change_record["size"] = size

                        checker.history.append(change_record)
                        checker._save_history()

                        print(
                            f"[{timestamp}] {file_path}: {change_type} - {description}"
                        )
                flash(f"Файл {filename} успішно збережено", "success")

    # Видалення файлу
    elif action == "delete" and filename:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f"Файл {filename} успішно видалено", "success")
            return redirect(url_for("list"))
        else:
            flash("Файл не знайдено", "danger")

    # Редагування файлу
    elif action == "edit" and filename:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
        if os.path.exists(file_path):
            content = read_file_content(file_path)
            return render_template("edit_file.html", filename=filename, content=content)
        else:
            flash("Файл не знайдено", "danger")
            return redirect(url_for("list"))

    # Відображення списку файлів
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    editable_files = [
        f for f in files if os.path.splitext(f)[1].lower() in [".txt", ".docx"]
    ]
    return render_template("files.html", files=editable_files)
