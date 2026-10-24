
import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb://127.0.0.1:27017"
)

MONGODB_DATABASE = os.getenv(
    "MONGODB_DATABASE",
    "credit_risk_nosql"
)

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=3000
)

db = client[MONGODB_DATABASE]
risk_reviews = db["risk_reviews"]


def check_mongodb():
    client.admin.command("ping")
    return True
