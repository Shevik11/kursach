from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from models import User
from app import db, bcrypt, app
from flask_login import login_user, logout_user, login_required
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity


auth_bp = Blueprint("auth", __name__)
jwt = JWTManager(app)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(
                "Username already taken. Please choose a different username.", "danger"
            )
            return render_template("register.html")
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully", "success")
        return redirect(url_for("auth.login"))  # Змінено з 'login' на 'auth.login'
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            access_token = create_access_token(identity=user.username)
            print(jsonify({"access_token": access_token}))
            return redirect(url_for("list"))
        else:
            flash("Невдалий вхід. Перевірте логін та пароль", "danger")
    return render_template("login.html")


@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з системи", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Hello, {current_user}!"}), 200
