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
    subject: ObjectId
    youtube: Optional[str] = None
    content: Any
