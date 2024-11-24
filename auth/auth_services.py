from dotenv import load_dotenv
import os
from .models import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")


default_user = User()


def login_user(email, password):
    # Аутентифікація користувача
    user = default_user.authenticate_user(email, password)
    user_id = user["localId"]

    # Перевірка, чи існує користувач у Firestore
    user_data = default_user.get_user_from_firestore(user_id)
    if not user_data.exists:
        raise ValueError("User data not found in Firestore")

    return {"user_id": user_id}


def register_user(email, password, username):
    try:
        # Create user in Firebase
        user = default_user.create_user_in_firebase(email, password)
        user_id = user["localId"]

        # Add user to Firestore
        default_user.add_user_to_firestore(email, username, user_id)

        return {"message": "User registered successfully"}
    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            return {"error": "This email address is already registered."}
        return {"error": error_message}
