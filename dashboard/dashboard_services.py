import os
from werkzeug.utils import secure_filename
from .dashboard_extensions import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, logger
from extensions import db
from flask import flash
from firebase_admin import firestore


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_path(username, filename):
    return os.path.join(UPLOAD_FOLDER, username, secure_filename(filename))


def get_user_data(user_id):
    """Отримує дані користувача з бази даних."""
    user_ref = db.collection("users").document(user_id)
    user_data = user_ref.get().to_dict()
    return user_ref, user_data


def create_user_folder(username):
    """Створює папку користувача, якщо вона ще не існує."""
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    return user_folder


def get_local_files(user_folder, username):
    """Отримує список локальних файлів користувача."""
    local_files = [
        {"name": filename, "url": f"/uploads/{username}/{filename}"}
        for filename in os.listdir(user_folder)
        if allowed_file(filename)
    ]
    local_files.sort(key=lambda x: x["name"])
    return local_files


def save_file(file, user_folder, username, user_ref):
    """Зберігає файл у папку користувача і оновлює базу даних."""
    filename = secure_filename(file.filename)
    file_path = os.path.join(user_folder, filename)
    print(filename, file_path)

    try:
        user_ref.update({"files": firestore.ArrayUnion([filename])})
        file.save(file_path)
        flash(f"File '{filename}' uploaded successfully!", "success")
        return {"name": filename, "url": f"/uploads/{username}/{filename}"}
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        flash(f"Error uploading file: {str(e)}", "error")
        return None


def handle_file_upload(
    request, user_data, user_folder, username, user_ref, local_files
):
    print(f"request: {request}, user_data: {user_data}, user_folder: {user_folder}, username: {username}, user_ref: {user_ref}, local_files: {local_files}")
    file = request.files["file"]
    if file and allowed_file(file.filename):
        if file.filename not in user_data.get("files", []):
            uploaded_file = save_file(file, user_folder, username, user_ref)
            if uploaded_file:
                local_files.append(uploaded_file)
        else:
            flash(f"File '{file.filename}' already exists.", "info")
