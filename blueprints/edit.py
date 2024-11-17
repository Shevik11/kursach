from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from firebase_admin import firestore
import secrets
import os
from datetime import datetime, timedelta

edit_blueprint = Blueprint('edit', __name__)
pending_changes = {}


@edit_blueprint.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # Якщо це GET запит, показуємо форму редагування
    if request.method == 'GET':
        file_path = os.path.join('uploads', filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                session['filename'] = filename
                session['original_content'] = file_content  # Зберігаємо оригінальний контент
            return render_template('edit.html', file_content=file_content)
        except Exception as e:
            flash('Помилка при відкритті файлу', 'error')
            return redirect(url_for('dashboard.dashboard'))

    # Якщо це POST запит (користувач натиснув "Зберегти")
    else:
        file_content = request.form.get('file_content')
        return render_template('confirm_changes.html',
                               file_content=file_content,
                               filename=filename)


@edit_blueprint.route('/save-with-description', methods=['POST'])
def save_with_description():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    file_content = request.form.get('file_content')
    description = request.form.get('change_description')
    filename = session.get('filename')
    original_content = session.get('original_content')

    # Генеруємо унікальний токен для підтвердження
    confirmation_token = secrets.token_urlsafe(32)

    # Зберігаємо дані про зміни
    pending_changes[confirmation_token] = {
        'user_id': session['user_id'],
        'filename': filename,
        'new_content': file_content,
        'original_content': original_content,
        'description': description,
        'timestamp': datetime.now(),
        'expires': datetime.now() + timedelta(hours=24)
    }

    # Формуємо посилання для підтвердження
    confirmation_link = url_for('edit.confirm_changes',
                                token=confirmation_token,
                                _external=True)

    flash(f'Посилання для підтвердження змін: {confirmation_link}', 'info')
    return redirect(url_for('dashboard.dashboard'))


@edit_blueprint.route('/confirm/<token>')
def confirm_changes(token):
    if token not in pending_changes:
        flash('Недійсне або застаріле посилання для підтвердження', 'error')
        return redirect(url_for('dashboard.dashboard'))

    change_data = pending_changes[token]

    # Перевіряємо чи не застарів токен
    if datetime.now() > change_data['expires']:
        pending_changes.pop(token)
        flash('Посилання для підтвердження застаріло', 'error')
        return redirect(url_for('dashboard.dashboard'))

    try:
        # Зберігаємо зміни у файл
        file_path = os.path.join('uploads', change_data['filename'])
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(change_data['new_content'])

        # Записуємо інформацію про зміни в базу даних
        db = firestore.client()
        db.collection('changes').add({
            'user_id': change_data['user_id'],
            'filename': change_data['filename'],
            'description': change_data['description'],
            'timestamp': firestore.SERVER_TIMESTAMP,
            'original_content': change_data['original_content'],
            'new_content': change_data['new_content']
        })

        # Видаляємо дані про очікуючі зміни
        pending_changes.pop(token)

        flash('Зміни успішно збережено!', 'success')
    except Exception as e:
        flash('Помилка при збереженні змін', 'error')

    return redirect(url_for('dashboard.dashboard'))