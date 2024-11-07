from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from main import FileWatcher
from file_manager import read_file_content, save_file_content
import docx  # Додаємо бібліотеку для роботи з docx
import mimetypes  # Для визначення типу файлу
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
checker = FileWatcher("./uploads", ['.txt', '.doc', '.docx', '.pdf'])

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose a different username.', 'danger')
            return render_template('register.html')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Ви успішно увійшли', 'success')
            return redirect(url_for('files'))
        else:
            flash('Невдалий вхід. Перевірте логін та пароль', 'danger')
    return render_template('login.html')



# Маршрут для роботи з файлами
@app.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    action = request.args.get('action')
    filename = request.args.get('filename')

    # Завантаження нового файлу
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            flash(f'Файл {filename} успішно завантажено', 'success')
            return redirect(url_for('files'))

    # Збереження відредагованого файлу
    elif request.method == 'POST' and 'content' in request.form and 'filename' in request.form:
        filename = request.form['filename']
        content = request.form['content']
        description = request.form['description']# Get the user-provided description

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            if save_file_content(file_path, content):
                current_states = checker._get_directory_state()
                changes = checker._detect_change_type(checker.last_states, current_states)
                for file_path, change_type, size in changes:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user = current_user.username
                    if change_type:
                        change_record = {
                            "file": str(file_path).split("\\")[-1],
                            "type": change_type,
                            "time": timestamp,
                            'user': user,
                            "description": description  # Add the description to the log
                        }
                        if size is not None:
                            change_record["size"] = size

                        checker.history.append(change_record)
                        checker._save_history()

                        print(f"[{timestamp}] {file_path}: {change_type} - {description}")
                flash(f'Файл {filename} успішно збережено', 'success')

    # Видалення файлу
    elif action == 'delete' and filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f'Файл {filename} успішно видалено', 'success')
            return redirect(url_for('files'))
        else:
            flash('Файл не знайдено', 'danger')

    # Редагування файлу
    elif action == 'edit' and filename:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        if os.path.exists(file_path):
            content = read_file_content(file_path)
            return render_template('edit_file.html', filename=filename, content=content)
        else:
            flash('Файл не знайдено', 'danger')
            return redirect(url_for('files'))

    # Відображення списку файлів
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    editable_files = [f for f in files if os.path.splitext(f)[1].lower() in ['.txt', '.docx']]
    return render_template('files.html', files=editable_files)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з системи", 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)