# src/mongo.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

from typing import Tuple

from settings import config


def connect() -> Tuple:
    try:
        client = AsyncIOMotorClient(config.MONGO_URI, server_api=ServerApi("1"))
        db = client["abokicode_db"]
        return client, db
    except Exception as E:
        raise Exception("Unable to connect: ", E)
