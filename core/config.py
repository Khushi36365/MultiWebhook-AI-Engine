import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URL = os.getenv("MONGO_URL")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")