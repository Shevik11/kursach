from dotenv import load_dotenv
import logging
from itsdangerous import URLSafeTimedSerializer
import os
# Завантаження змінних середовища
load_dotenv()

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Ініціалізація токенів
s = URLSafeTimedSerializer(os.getenv("SECRET_KEY"))

# Налаштування завантаження файлів
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "docx"}