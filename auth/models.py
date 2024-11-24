# models.py
from extensions import pyrebase_auth, db


class User:
    def __init__(self):
        self.user_id = None

    def create_user_in_firebase(self, email, password):
        user = pyrebase_auth.create_user_with_email_and_password(email, password)
        user_id = user["localId"]
        return user

    def add_user_to_firestore(self, email, username, user_id):
        if user_id:
            db.collection("users").document(user_id).set(
                {"email": email, "username": username}
            )
        else:
            raise ValueError("User ID is not set. Create user in Firebase first.")

    @staticmethod
    def get_user_from_firestore(user_id):
        return db.collection("users").document(user_id).get()

    def authenticate_user(self, email, password):
        return pyrebase_auth.sign_in_with_email_and_password(email, password)
