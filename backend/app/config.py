import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in .env")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env")