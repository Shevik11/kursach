from flask import Blueprint, render_template, request, session, redirect, url_for, flash
import os
from google.cloud import firestore
from docx import Document
from .dashboard_extensions import UPLOAD_FOLDER, logger, ALLOWED_EXTENSIONS
from extensions import db, mail



def get_file_path(username, filename):
    """Отримує повний шлях до файлу користувача."""
    return os.path.join(UPLOAD_FOLDER, username, filename)

def get_username(user_id):
    """Отримує ім'я користувача з бази даних."""
    user_data = db.collection("users").document(user_id).get().to_dict()
    return user_data.get("username", user_id)

def remove_file_and_update_db(user_ref, file_path, filename):
    """Видаляє файл і оновлює базу даних."""
    if os.path.exists(file_path):
        os.remove(file_path)
        user_ref.update({"files": firestore.ArrayRemove([filename])})
        flash(f"File '{filename}' deleted successfully.", "success")
    else:
        flash(f"File '{filename}' does not exist.", "error")

def read_file_content(file_path, filename):
    """Зчитує вміст файлу."""
    if filename.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    elif filename.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        return None