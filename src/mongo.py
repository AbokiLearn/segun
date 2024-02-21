# src/mongo.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from bson import ObjectId

from pydantic import BaseModel
from typing import List, Tuple

from models import AtlasVectorSearch, RetrievedLecture
from settings import config
from llm import embed_async


def connect() -> Tuple:
    """Establish connection to databse"""
    try:
        client = AsyncIOMotorClient(config.MONGO_URI, server_api=ServerApi("1"))
        db = client["abokicode_db"]
        return client, db
    except Exception as E:
        raise Exception("Unable to connect: ", E)


async def get_subjects(db) -> List[dict]:
    """Retrieve all records from the `subjects` collection."""
    subjects_cursor = db["subjects"].find()
    subjects = []
    async for subject in subjects_cursor:
        subjects.append(subject)
    return subjects


async def fetch(
    db, _id: str, collection: str, response_model: BaseModel | None = None
) -> dict:
    """Retrieve a record by _id from a specified collection."""
    document = await db[collection].find_one({"_id": ObjectId(_id)})

    if document:
        return response_model(**document) if response_model else document
    return {}


async def vector_search(
    db,
    query: str,
    top_k: int = 3,
    subject_ids: List[str] = [],
    lecture_ids: List[str] = [],
    n_candidates: int = 200,
) -> List[dict]:
    """Run similarity search against the `lecture-index` and return results as a list."""
    query_vector = await embed_async(query)

    pipeline = AtlasVectorSearch(
        query_vector=query_vector,
        n_candidates=n_candidates,
        top_k=top_k,
        subject_filter=subject_ids,
        lecture_filter=lecture_ids,
    ).mkpipeline()

    cr = db["lecture_chunks"].aggregate(pipeline)
    results = []
    async for doc in cr:
        subject = await fetch(db, doc["subject_id"], "subjects")
        lecture = await fetch(db, doc["lecture_id"], "lectures")
        results.append(
            RetrievedLecture(
                **{**doc, "subject": subject["title"], "lecture": lecture["title"]}
            )
        )

    return results
