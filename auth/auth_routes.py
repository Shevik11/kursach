from flask import request, jsonify, render_template, session, redirect, url_for, flash
from .auth_blueprint import auth_blueprint
from .auth_services import register_user, login_user


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            email = request.form.get("email")

            response = register_user(email, password, username)
            return jsonify(response), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template("register.html")


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            # Виклик сервісу входу
            user_session = login_user(email, password)

            if user_session:
                session["user_id"] = user_session["user_id"]
                return redirect(url_for("dashboard.dashboard"))
            else:
                flash("Invalid login credentials. Please try again.", "error")
    except Exception as e:
        print(f"Error: {e}")
        flash("An error occurred. Please try again later.", "error")
    return render_template("login.html")
