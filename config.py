import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
TOKEN = os.getenv("TOKEN")
DATABASE_NAME = os.getenv("DATABASE_NAME", "blackflames")
CHALLONGE_API_KEY = os.getenv("CHALLONGE_API_KEY")
CHALLONGE_USERNAME = "HI__Kai"
