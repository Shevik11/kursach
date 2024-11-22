from .dashboard_extensions import s, logger, UPLOAD_FOLDER
import os
from docx import Document
from flask_mail import Message
from extensions import mail
from flask import session
def get_file_path(username, filename):
    """Отримує повний шлях до файлу."""
    return os.path.join(UPLOAD_FOLDER, username, filename)

def get_file_content(file_path, filename):
    """Зчитує поточний вміст файлу."""
    if filename.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif filename.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    return None

def save_change_token(filename, user_id, new_content, description):
    """Створює токен для підтвердження змін."""
    token_data = {
        "filename": filename,
        "user_id": user_id,
    }
    session["new_content"] = new_content
    session["description"] = description
    return s.dumps(token_data, salt="confirm-change")

def send_confirmation_email(email, filename, confirm_url):
    """Надсилає електронний лист для підтвердження змін."""
    msg = Message(f"Підтвердження змін у файлі {filename}", recipients=[email])
    msg.body = f"Щоб підтвердити зміни до файлу {filename}, перейдіть за посиланням: {confirm_url}"
    mail.send(msg)