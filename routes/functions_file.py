from flask import request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
import os
from app import app
from main import FileWatcher
from utils import read_file_content, save_file_content
from datetime import datetime
from flask_login import current_user



checker = FileWatcher("./uploads", [".txt", ".doc", ".docx", ".pdf"])


def upload_file():
    file = request.files["file"]
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        flash(f"Файл {filename} успішно завантажено", "success")
    return redirect(url_for("list"))


def save_file():
    filename = request.form["filename"]
    content = request.form["content"]
    description = request.form["description"]

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
    if os.path.exists(file_path) and save_file_content(file_path, content):
        current_states = checker._get_directory_state()
        changes = checker._detect_change_type(checker.last_states, current_states)
        for file_path, change_type, size in changes:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user = current_user.username
            change_record = {
                "file": str(file_path).split("\\")[-1],
                "type": change_type,
                "time": timestamp,
                "user": user,
                "description": description,
            }
            if size is not None:
                change_record["size"] = size
            checker.history.append(change_record)
            checker._save_history()
            print(f"[{timestamp}] {file_path}: {change_type} - {description}")
        flash(f"Файл {filename} успішно збережено", "success")
    return redirect(url_for("list"))


def delete_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"Файл {filename} успішно видалено", "success")
    else:
        flash("Файл не знайдено", "danger")
    return redirect(url_for("list"))


def edit_file(filename):
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
    if os.path.exists(file_path):
        content = read_file_content(file_path)
        return render_template("edit_file.html", filename=filename, content=content)
    else:
        flash("Файл не знайдено", "danger")
        return redirect(url_for("list"))


def list_files():
    files = os.listdir(app.config["UPLOAD_FOLDER"])
    editable_files = [f for f in files if os.path.splitext(f)[1].lower() in [".txt", ".docx"]]
    return render_template("files.html", files=editable_files)