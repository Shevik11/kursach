import os
from flask import render_template, request, session, redirect, url_for, flash
from extensions import db
from itsdangerous import BadSignature, SignatureExpired
from .dashboard_services import (
    get_user_data,
    get_local_files,
    create_user_folder,
    handle_file_upload,
)
from .dashboard_extensions import logger
from .delete_services import (
    get_username,
    get_file_path,
    remove_file_and_update_db,
    read_file_content,
)
from .dashhboard_email_services import (
    get_user_id_from_session,
    handle_expired_session,
    validate_token,
    get_session_data,
    get_username_from_db,
    update_file,
    update_database,
)
from .dashboard_blueprint import dashboard_blueprint
from .dashboard_edit_services import (
    get_file_content,
    handle_edit_post_request,
)
from .models import UserFileModel


@dashboard_blueprint.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    user_ref, user_data = UserFileModel.get_user_data(user_id)

    if not user_data:
        flash("User data not found.", "error")
        return redirect(url_for("auth.login"))

    username = user_data.get("username", user_id)
    user_folder = create_user_folder(username)
    local_files = get_local_files(user_folder, username)
    print(f"local: {local_files}")

    if request.method == "POST":
        handle_file_upload(
            request, user_data, user_folder, username, user_ref, local_files
        )

    return render_template("index.html", files=local_files)


@dashboard_blueprint.route("/delete_file/<filename>", methods=["POST"])
def delete_file(filename):
    try:
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        user_id = session["user_id"]
        user_ref = db.collection("users").document(user_id)
        username = get_username(user_id)
        file_path = get_file_path(username, filename)

        remove_file_and_update_db(user_ref, file_path, filename)
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        flash(f"Error deleting file: {str(e)}", "error")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_blueprint.route("/view_file/<filename>", methods=["GET"])
def view_file(filename):
    try:
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        user_id = session["user_id"]
        username = get_username(user_id)
        file_path = get_file_path(username, filename)

        if not os.path.exists(file_path):
            flash(f"File '{filename}' does not exist.", "error")
            return redirect(url_for("dashboard.dashboard"))

        content = read_file_content(file_path, filename)
        if content is None:
            flash("Unsupported file type.", "error")
            return redirect(url_for("dashboard.dashboard"))

        return render_template("view_file.html", filename=filename, content=content)
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        flash(f"Error reading file: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard"))


@dashboard_blueprint.route("/confirm_change/<token>/<filename>", methods=["GET"])
def confirm_change(token, filename):
    """Основний обробник підтвердження змін."""
    try:
        user_id = get_user_id_from_session()
        print(f"user_id: {user_id}")
        if not user_id:
            return handle_expired_session()

        data = validate_token(token)
        new_content, description = get_session_data()
        username = get_username_from_db(user_id)
        file_path = get_file_path(username, filename)
        update_file(file_path, filename, new_content)
        update_database(user_id, filename, description, username)
        flash("Зміни підтверджено.", "success")
        return redirect(url_for("dashboard.dashboard"))

    except SignatureExpired:
        flash("Посилання для підтвердження зміни втратило актуальність.", "error")
    except BadSignature:
        flash("Недійсне посилання для підтвердження.", "error")
    except Exception as e:
        logger.error(f"Помилка підтвердження змін: {str(e)}")
        flash(f"Помилка підтвердження змін: {str(e)}", "error")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_blueprint.route("/edit_file/<filename>", methods=["GET", "POST"])
def edit_file(filename):
    try:
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        user_id = session["user_id"]
        user_ref, user_data = get_user_data(user_id)

        if not user_data:
            flash("Користувача не знайдено.", "error")
            return redirect(url_for("auth.login"))

        username = user_data.get("username", user_id)
        file_path = get_file_path(username, filename)

        if not os.path.exists(file_path):
            flash(f"Файл '{filename}' не існує.", "error")
            return redirect(url_for("dashboard.dashboard"))

        current_content = get_file_content(file_path, filename)
        if current_content is None:
            flash("Непідтримуваний формат файлу.", "error")
            return redirect(url_for("dashboard.dashboard"))

        if request.method == "POST":
            return handle_edit_post_request(
                request, filename, user_id, user_data, current_content
            )

        return render_template(
            "edit_file.html", filename=filename, content=current_content
        )
    except Exception as e:
        logger.error(f"Помилка під час редагування файлу: {str(e)}")
        flash(f"Помилка під час редагування файлу: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard"))
