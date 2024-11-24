from .dashboard_extensions import s, logger
from docx import Document
from flask_mail import Message
from extensions import mail
from flask import session, redirect, url_for, flash


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


def handle_edit_post_request(request, filename, user_id, user_data, current_content):
    new_content = request.form.get("content")
    if not new_content:
        flash("Не вказано новий вміст для файлу.", "error")
        return redirect(url_for("dashboard.dashboard"))

    description = request.form.get("description", "")
    token = save_change_token(filename, user_id, new_content, description)
    confirm_url = url_for(
        "dashboard.confirm_change", token=token, _external=True, filename=filename
    )

    try:
        send_confirmation_email(user_data["email"], filename, confirm_url)
        flash("Зміни збережено. Перевірте свою пошту для підтвердження.", "success")
    except Exception as e:
        logger.error(f"Не вдалося надіслати лист: {str(e)}")
        flash("Не вдалося надіслати лист для підтвердження. Спробуйте ще раз.", "error")

    return redirect(url_for("dashboard.dashboard"))
