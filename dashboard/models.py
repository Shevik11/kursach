from extensions import db
import datetime
from google.cloud import firestore


class UserFileModel:
    """Модель для роботи з файлами користувачів у базі даних."""

    @staticmethod
    def get_user_data(user_id):
        user_ref = db.collection("users").document(user_id)
        return user_ref, user_ref.get().to_dict()

    @staticmethod
    def update_user_files(user_id, filename, action="add"):
        user_ref = db.collection("users").document(user_id)
        if action == "add":
            user_ref.update({"files": firestore.ArrayUnion([filename])})
        elif action == "remove":
            user_ref.update({"files": firestore.ArrayRemove([filename])})

    @staticmethod
    def log_file_change(user_id, filename, description, username):
        user_ref = db.collection("users").document(user_id)
        user_ref.update(
            {
                "file_changes": firestore.ArrayUnion(
                    [
                        {
                            "filename": filename,
                            "description": description,
                            "timestamp": datetime.datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "modified_by": username,
                        }
                    ]
                )
            }
        )
