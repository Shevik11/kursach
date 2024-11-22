from extensions import pyrebase_auth, db

def register_user(username, email, password):
    # Створення користувача через Firebase
    user = pyrebase_auth.create_user(email=email, password=password)
    # Додавання до Firestore
    db.collection("users").document(user["localId"]).set({"email": email, "username": username})
    return {"message": "User registered successfully"}


def login_user(email, password):
    # Аутентифікація користувача через Pyrebase
    user = pyrebase_auth.sign_in_with_email_and_password(email, password)
    user_data = db.collection("users").document(user["localId"]).get()

    if not user_data.exists:
        raise ValueError("User data not found in Firestore")

    return {"user_id": user["localId"]}
