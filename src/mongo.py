# src/mongo.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

from typing import List, Tuple

from models import AtlasVectorSearch
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


async def search(
    db,
    query: str,
    top_k: int = 5,
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
        results.append(doc)

    return results
