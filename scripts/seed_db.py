# scripts/seed_db.py

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import asyncio

from llama_index.core.node_parser import MarkdownNodeParser
from llama_index.readers.file import FlatReader

from rich import print
from tqdm import tqdm

from typing import Dict, Tuple, List
from pathlib import Path
import sys
import re
import aiofiles

sys.path.append("src")
from models import Subject, Lecture, LectureChunk
from settings import config
from llm import embed


async def get_lectures() -> List[Path]:
    path = Path("./data/js-lectures").resolve()

    if not path.exists():
        print("[red]seed failed: `data/js-lectures` not found[/red]")
        sys.exit(1)

    return sorted(path.glob("*.md"))


async def extract_metadata(filepath: Path) -> Tuple[int, str, str]:
    filename = filepath.name
    pattern = r"(\d+)-\[(.*?)\]-(.*?)\.md"
    match = re.search(pattern, filename)

    if not match:
        raise ValueError(f"Filename {filename} does not match expected pattern.")

    lecture_num, subject_raw, title_raw = match.groups()
    subject = subject_raw.replace("-", " ").capitalize()
    title = title_raw.replace("-", " ").capitalize()
    return int(lecture_num), subject, title


async def load_md_str(filepath: Path) -> str:
    async with aiofiles.open(filepath, "r", encoding="utf-8") as file:
        return await file.read()


async def init_database(db):
    await db["subjects"].drop()
    await db["lectures"].drop()
    await db["lecture_chunks"].drop()
    await db.create_collection("subjects")
    await db.create_collection("lectures")
    await db.create_collection("lecture_chunks")
    await db["subjects"].create_index([("title", 1)], unique=True)
    await db["lectures"].create_index([("idx", 1)], unique=True)


async def process_lectures(db, lectures) -> Dict:
    subjects = {}
    lecture_info = {}

    for lecture in tqdm(lectures, total=len(lectures), desc="seeding database"):
        idx, subject, title = await extract_metadata(lecture)
        content = await load_md_str(lecture)

        if subject not in subjects:
            subject_document = Subject(title=subject, lectures=[]).dump("upload")
            res_s = await db["subjects"].insert_one(subject_document)
            subjects[subject] = {"id": res_s.inserted_id, "lectures": []}

        lecture_document = Lecture(
            idx=idx, title=title, subject_id=subjects[subject]["id"], content=content
        ).dump("upload")
        res_l = await db["lectures"].insert_one(lecture_document)

        subjects[subject]["lectures"].append(res_l.inserted_id)
        lecture_info[str(lecture)] = {
            "subject": res_s.inserted_id,
            "lecture": res_l.inserted_id,
        }

    for subject, details in tqdm(
        subjects.items(), total=len(subjects), desc="updating subjects"
    ):
        await db["subjects"].update_one(
            {"_id": details["id"]}, {"$set": {"lectures": details["lectures"]}}
        )

    return lecture_info


async def chunk_and_embed(db, lecture_info):
    reader = FlatReader()
    parser = MarkdownNodeParser()

    for filepath, identifiers in tqdm(
        lecture_info.items(),
        total=len(lecture_info),
        desc="chunking & embedding lectures...",
    ):
        doc = reader.load_data(Path(filepath))
        chunks = [
            chk.text for chk in parser.get_nodes_from_documents(doc) if chk.text != ""
        ]
        embeddings = embed(chunks)

        lecture_chunks = [
            LectureChunk(
                subject_id=identifiers["subject"],
                lecture_id=identifiers["lecture"],
                chunk=chk,
                embedding=embedding,
            ).dump("upload")
            for chk, embedding in zip(chunks, embeddings)
        ]

        await db["lecture_chunks"].insert_many(lecture_chunks)


async def main():
    print("[cyan]seeding 'lectures' and 'subjects' collections[/cyan]")
    client = AsyncIOMotorClient(config.MONGO_URI, server_api=ServerApi("1"))
    db = client["abokicode_db"]
    await init_database(db)
    lectures = await get_lectures()
    lecture_info = await process_lectures(db, lectures)
    print("[green]done 😊[/green]", end="\n\n")

    print("[cyan]seeding lecture_chunks[/cyan]")
    await chunk_and_embed(db, lecture_info)
    print("[green]done 😊[/green]")


if __name__ == "__main__":
    asyncio.run(main())
