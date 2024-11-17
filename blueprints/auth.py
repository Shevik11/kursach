from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from extensions import db
import pyrebase
from extensions import pyrebase_auth, auth, db
import logging
logging.basicConfig(level=logging.DEBUG)

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        try:
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')

            # Створити користувача через Firebase Admin SDK
            user = auth.create_user(email=email, password=password)

            # Додати користувача до Firestore
            db.collection('users').document(user.uid).set({
                "email": email,
                "username": username
            })

            return jsonify({"message": "User registered successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template('register.html')

@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    print('bla bla ')
    try:
        if request.method == 'POST':
            # Getting form data
            email = request.form['email']
            password = request.form['password']
            print("1. Starting login process")
            print(f"2. Got login data: {email}")

            # Authentication with Pyrebase
            print("3. Attempting to authenticate with Pyrebase")
            user = pyrebase_auth.sign_in_with_email_and_password(email, password)
            print(f"4. User authenticated with ID: {user['localId']}")

            # Fetch user data from Firestore (if needed)
            user_data = db.collection('users').document(user['localId']).get()  # Використовуємо Firestore для отримання даних

            if not user_data.exists:
                raise ValueError("User data not found in Firestore")

            print("6. User data fetched successfully")

            # Set user session data
            session['user_id'] = user['localId']

            # Redirect to dashboard
            return redirect(url_for("dashboard.dashboard"))

    except Exception as e:
        print(f"Error: {e}")
    return render_template('login.html')
