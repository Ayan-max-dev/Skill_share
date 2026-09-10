from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = "sqlite:///skillshare.db"

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is not set")