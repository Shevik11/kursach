from flask import request, jsonify, render_template, session, redirect, url_for, flash
from .dashboard_extensions import s, logger, UPLOAD_FOLDER
import os
import datetime
from google.cloud import firestore
from docx import Document
from extensions import db

def get_user_id_from_session():
    """Отримує ідентифікатор користувача з сесії."""
    return session.get("user_id")


def handle_expired_session():
    """Обробка завершення сесії."""
    flash("Сеанс завершено. Будь ласка, увійдіть знову.", "error")
    return redirect(url_for("auth.login"))


def validate_token(token):
    """Валідація токена для підтвердження змін."""
    return s.loads(token, salt="confirm-change", max_age=3600)


def get_session_data():
    """Отримує дані з сесії."""
    new_content = session.get("new_content")
    description = session.get("description")
    print(f"new_content: {new_content}, description: {description}")
    if not new_content:
        logger.error("Не знайдено новий вміст для файлу у сесії.")
        flash("Не знайдено новий вміст для файлу.", "error")
        raise ValueError("Новий вміст не знайдено.")
    return new_content, description


def get_username_from_db(user_id):
    """Отримує ім'я користувача з бази даних."""
    user_data = db.collection("users").document(user_id).get().to_dict()
    return user_data.get("username", user_id)


def get_file_path(username, filename):
    """Формує шлях до файлу користувача."""
    return os.path.join(UPLOAD_FOLDER, username, filename)


def update_file(file_path, filename, new_content):
    """Оновлює вміст файлу."""
    if filename.endswith(".txt"):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    elif filename.endswith(".docx"):
        doc = Document()
        for line in new_content.split("\n"):
            doc.add_paragraph(line)
        doc.save(file_path)


def update_database(user_id, filename, description, username):
    """Оновлює інформацію про зміну файлу в базі даних."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_ref = db.collection("users").document(user_id)
    user_ref.update(
        {
            "file_changes": firestore.ArrayUnion(
                [
                    {
                        "filename": filename,
                        "description": description,
                        "timestamp": timestamp,
                        "modified_by": username,
                    }
                ]
            )
        }
    )