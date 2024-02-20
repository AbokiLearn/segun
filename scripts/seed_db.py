#!/usr/bin/env .venv/bin/python

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from rich import print
from tqdm import tqdm
import asyncio
import pymongo

from typing import Tuple, List
from pathlib import Path
import sys
import re
import aiofiles

sys.path.append("src")
from models import Subject, Lecture
from settings import config


async def get_lectures() -> List[Path]:
    path = Path("./data/js-lectures").resolve()

    if not path.exists():
        print("[red]seed failed: `data/js-lectures` not found[/red]")
        sys.exit(1)

    return list(path.glob("*.md"))


async def extract_metadata(filepath: Path) -> Tuple[int, str, str]:
    filename = filepath.name
    pattern = r"(\d+)-\[(.*?)\]-(.*?)\.md"
    match = re.search(pattern, filename)
    if match:
        lectureNum = int(match.group(1))
        subject = " ".join(match.group(2).split("-")).capitalize()
        title = " ".join(match.group(3).split("-")).capitalize()
        return lectureNum, subject, title
    else:
        raise ValueError(f"Filename {filename} does not match expected pattern.")


async def load_md_str(filepath: Path) -> str:
    async with aiofiles.open(filepath, "r", encoding="utf-8") as file:
        return await file.read()


async def main():
    print(
        "[green]seeding `abokicode_db:lectures` with content from `data/js-lectures`[/green]"
    )

    client = AsyncIOMotorClient(config.MONGO_URI, server_api=ServerApi("1"))
    db = client["abokicode_db"]

    await db["subjects"].drop()
    await db["lectures"].drop()

    await db.create_collection("subjects")
    await db.create_collection("lectures")
    await db["subjects"].create_index([("title", 1)], unique=True)
    await db["lectures"].create_index([("idx", 1)], unique=True)

    lectures = await get_lectures()

    subjects = {}
    for lecture in tqdm(lectures, desc="seeding `subjects`"):
        try:
            _, subject, _ = await extract_metadata(lecture)
            subject_document = Subject(title=subject, lectures=[]).dump("upload")
            try:
                result = await db["subjects"].insert_one(subject_document)
                subjects[subject] = result.inserted_id
            except pymongo.errors.DuplicateKeyError:
                continue
        except ValueError:
            print(f"[red]Error encountered for {lecture}[red]")

    for lecture in tqdm(lectures, desc="seeding `lectures`"):
        try:
            idx, subject, title = await extract_metadata(lecture)
            content = await load_md_str(lecture)
            lecture_document = Lecture(
                idx=idx, title=title, subject=subjects[subject], content=content
            ).dump("upload")

            result = await db["lectures"].insert_one(lecture_document)
            await db["subjects"].update_one(
                {"_id": subjects[subject]}, {"$push": {"lectures": result.inserted_id}}
            )
        except ValueError:
            print(f"[red]Error encountered for {lecture}[red]")

    print("[green]done 😊[/green]")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
