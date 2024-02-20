# src/models

from pydantic import BaseModel, Field
from bson import ObjectId

from typing import Any, List, Optional


class MongoDocument(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
        json_encoders = {ObjectId: str}

    def dump(self, type_: str = "upload"):
        """dump model to dictionary"""
        d = self.model_dump()
        if type_ == "upload":
            del d["id"]
        return d


class Subject(MongoDocument):
    title: str
    lectures: Optional[List[ObjectId]] = None


class Lecture(MongoDocument):
    idx: int
    title: str
    subject_id: ObjectId
    youtube: Optional[str] = None
    content: Any


class LectureChunk(MongoDocument):
    subject_id: str
    lecture_id: str
    chunk: str
    embedding: List[float]


class AtlasVectorSearch(BaseModel):
    index: str = "lecture-index"
    path: str = "embedding"
    query_vector: List[float]
    n_candidates: int
    top_k: int
    subject_filter: List[str]
    lecture_filter: List[str]

    def mkpipeline(self):
        """Construct pipeline for Atlas Search"""
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self.index,
                    "path": self.path,
                    "queryVector": self.query_vector,
                    "numCandidates": self.n_candidates,
                    "limit": self.top_k,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "subject_id": 1,
                    "lecture_id": 1,
                    "chunk": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]

        filter_ = []
        if self.subject_filter != []:
            filter_.append({"subject_id": {"$in": self.subject_filter}})
        if self.lecture_filter != []:
            filter_.append({"lecture_id": {"$in": self.lecture_filter}})

        if len(filter_) == 1:
            pipeline[0]["$vectorSearch"]["filter"] = filter_[0]
        elif len(filter_) == 2:
            pipeline[0]["$vectorSearch"]["filter"] = {"$or": filter_}

        return pipeline
