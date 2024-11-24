from flask_mail import Mail
import pyrebase
import os
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
from firebase_admin import storage

load_dotenv()
import firebase_admin

# Ініціалізація Firebase Admin SDK

if not firebase_admin._apps:
    # Only initialize if Firebase hasn't been initialized yet
    cred = credentials.Certificate("./admin.json")
    firebase_admin.initialize_app(
        cred,
        {
            "storageBucket": "courseproj-d97be.firebasestorage.app"  # Correct bucket name
        },
    )

# Ініціалізація Pyrebase
firebase_config = {
    "apiKey": os.getenv("apiKey"),
    "authDomain": os.getenv("authDomain"),
    "databaseURL": os.getenv("databaseURL"),
    "projectId": os.getenv("projectId"),
    "storageBucket": os.getenv("storageBucket"),
    "messagingSenderId": os.getenv("messagingSenderId"),
    "appId": os.getenv("appId"),
}

pyrebase_app = pyrebase.initialize_app(firebase_config)
pyrebase_auth = pyrebase_app.auth()
db = firestore.client()

# Ініціалізація Flask-Mail
mail = Mail()
f_bucket = storage.bucket(os.getenv("storageBucket"))


UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "docx"}
