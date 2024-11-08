from flask import Blueprint, render_template, redirect, url_for, request, flash
from models import User
from app import db, bcrypt
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint("auth", __name__)


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
            return redirect(url_for("list"))  # перенаправляємо на /files/
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
