import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from extensions import db, mail
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .dashboard_services import get_user_data, get_local_files, create_user_folder, allowed_file, save_file, get_file_path
from .dashboard_extensions import logger
from .delete_services import get_username, get_file_path, remove_file_and_update_db, read_file_content
from .dashhboard_email_services import get_user_id_from_session, handle_expired_session, validate_token, get_session_data, get_username_from_db, update_file, update_database
from .dashboard_blueprint import dashboard_blueprint
from .dashboard_edit_services import get_file_path, get_file_content, save_change_token, send_confirmation_email

@dashboard_blueprint.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    user_ref, user_data = get_user_data(user_id)

    if not user_data:
        flash("User data not found.", "error")
        return redirect(url_for("auth.login"))

    username = user_data.get("username", user_id)
    user_folder = create_user_folder(username)
    local_files = get_local_files(user_folder, username)
    print(f"local: {local_files}")

    if request.method == "POST":
        file = request.files["file"]
        if file and allowed_file(file.filename):
            if file.filename not in user_data.get("files", []):
                uploaded_file = save_file(file, user_folder, username, user_ref)
                if uploaded_file:
                    local_files.append(uploaded_file)
            else:
                flash(f"File '{file.filename}' already exists.", "info")

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
        print(f" data: {data} new_content: {new_content}, description: {description}")
        username = get_username_from_db(user_id)
        file_path = get_file_path(username, filename)
        print(f"username: {username}, file_path: {file_path}")
        update_file(file_path, filename, new_content)
        update_database(user_id, filename, description, username)
        print(f"update_file: {update_file}, update_database: {update_database}")
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
        user_ref = db.collection("users").document(user_id)
        user_data = user_ref.get().to_dict()

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
            new_content = request.form.get("content")
            logger.info(f"Новий вміст: {new_content}")
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

        return render_template(
            "edit_file.html", filename=filename, content=current_content
        )
    except Exception as e:
        logger.error(f"Помилка під час редагування файлу: {str(e)}")
        flash(f"Помилка під час редагування файлу: {str(e)}", "error")
        return redirect(url_for("dashboard.dashboard"))