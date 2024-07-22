# src/llm.py

from sentence_transformers import SentenceTransformer
import torch

from langsmith.wrappers import wrap_openai
from langsmith import traceable

from concurrent.futures import ThreadPoolExecutor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, field_validator
import instructor
import asyncio

from typing import List
from enum import Enum

from settings import config
from models import Message, RetrievedLecture

executor = ThreadPoolExecutor()
encoder = SentenceTransformer(config.EMBEDDING_MODEL)
device = "cuda" if torch.cuda.is_available() else "cpu"

client = wrap_openai(
    AsyncOpenAI(
        api_key=config.OPENAI_API_KEY,
        # api_key=config.TOGETHER_API_KEY,
        # base_url="https://api.together.xyz/v1",
    )
)
client = instructor.patch(client, mode=instructor.Mode.TOOLS)
sem = asyncio.Semaphore(5)  # rate limit


def embed(
    texts: List[str] | str, batch_size: int = 64
) -> List[List[float]] | List[float]:
    if isinstance(texts, str):
        embeddings = encoder.encode(
            [texts],
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=1,
            device=device,
        ).tolist()[0]
    else:
        embeddings = encoder.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=batch_size,
            device=device,
        ).tolist()

    return embeddings


async def embed_async(
    texts: List[str] | str, batch_size: int = 64
) -> List[List[float]] | List[float]:
    loop = asyncio.get_event_loop()

    if isinstance(texts, str):
        embeddings = await loop.run_in_executor(
            executor,
            lambda: encoder.encode(
                [texts],
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=1,
                device=device,
            ).tolist()[0],
        )
    else:
        embeddings = await loop.run_in_executor(
            executor,
            lambda: encoder.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=batch_size,
                device=device,
            ).tolist(),
        )

    return embeddings


class QuestionUnderstanding(BaseModel):
    """
    You are a professor teaching a course on full-stack web development.
    One of your students has asked a question related to course material, but
    may not have phrased the question perfectly.
    Think about what the student is asking in the context of the course material.
    Then paraphrase their question to make it more explicit.
    """

    chain_of_thought: str = Field(
        ..., description="The chain of thought that led to this question."
    )
    question: str = Field(
        ..., description="A clearly stated question that is related to course material."
    )


class SubjectType(Enum):
    GETTING_STARTED = "Getting started"
    FIRST_STEPS = "First steps"
    CODE_QUALITY = "Code quality"
    OBJECT_BASICS = "Object basics"
    DATA_TYPES = "Data types"
    ADVANCED_FUNCTIONS = "Advanced functions"
    OBJECT_PROPERTIES = "Object properties"
    PROTOTYPES = "Prototypes"
    CLASSES = "Classes"
    ERROR_HANDLING = "Error handling"
    ASYNC = "Async"
    GENERATORS_ITERATORS = "Generators iterators"
    MODULES = "Modules"
    JS_MISC = "Js misc"


class QuestionSubject(BaseModel):
    """
    Predict the subject(s) that the question is asking about.
    Here are the available subjects:
    - 'Getting started'
    - 'First steps'
    - 'Code quality'
    - 'Object basics'
    - 'Data types'
    - 'Advanced functions'
    - 'Object properties'
    - 'Prototypes'
    - 'Classes'
    - 'Error handling'
    - 'Async'
    - 'Generators iterators'
    - 'Modules'
    - 'Js misc'
    """

    chain_of_thought: str = Field(
        ..., description="The chain of thought that led to the classification"
    )
    subjects: List[SubjectType] = Field(
        ...,
        description=f"An accurate and correct predicted subject of the question. Only allowed types: {[t.value for t in SubjectType]}, should be used.",
    )

    @field_validator("subjects", mode="before")
    def validate_subjects(cls, v):
        if not isinstance(v, list):
            v = [v]
        return v


@traceable(name="extract-question")
async def extract_question(user_question: str) -> QuestionUnderstanding:
    """Use LLM to expand on user's question"""

    async with sem:
        return user_question, await client.chat.completions.create(
            model=config.LLM,
            response_model=QuestionUnderstanding,
            max_retries=2,
            messages=[
                Message(
                    role="user",
                    content=f"Figure out what this question is trying to ask: {user_question}",
                ).model_dump()
            ],
            # max_tokens=1024,
        )


@traceable(name="determine-subject")
async def determine_subject(question: QuestionUnderstanding) -> str:
    """Use LLM to determine the subject of the question"""

    async with sem:
        return question, await client.chat.completions.create(
            model=config.LLM,
            response_model=QuestionSubject,
            max_retries=2,
            messages=[
                Message(
                    role="user",
                    content=f"Determine the subject of this question: {question}",
                ).model_dump()
            ],
            # max_tokens=1024,
        )


class AIAnswer(BaseModel):
    """The answer to a user's question. If the context documents provided are relevant, use them to guide your answer. If they are not relevant to the question, ignore them and do not mention them in the answer."""

    chain_of_thought: str = Field(
        ..., description="The chain of thought that led to this classification."
    )
    answer: str = Field(
        ..., description="A concise, accurate answer to the user's question."
    )
    relevance: int = Field(
        ...,
        description="""\
How relevant the answer is to the question and the provided context.

On a scale of 1 to 5; a score of 1 indicates the answer does not rely on the \
context at all; a score of 5 indicates the answer makes intelligent use of the \
provided context.
""",
    )
    sources: List[str] = Field(
        ...,
        description="A list of the lecture titles for each document used to answer the question.",
    )


@traceable(name="answer-question")
async def answer_question(
    question: str, context_docs: List[RetrievedLecture]
) -> AIAnswer:
    """Use LLM to answer the question"""

    docs_str = f"{'-' * 80}\n".join([str(doc) for doc in context_docs])

    async with sem:
        return await client.chat.completions.create(
            model=config.LLM,
            response_model=AIAnswer,
            max_retries=2,
            messages=[
                Message(
                    role="system",
                    content="""\
You are a senior full stack engineer at Evil inc.

You are currently teaching a team of new interns an introductory course on \
full-stack development. Answer the students questions using ONLY information \
from retrieved from your lecture notes.

Your answers must be concise and acccurate.
""",
                ).model_dump(),
                Message(
                    role="user",
                    content=f"""\
Here is my question '{question}'

Here are the relevant documents from the lecture notes:
{docs_str}
""",
                ).model_dump(),
            ],
            # max_tokens=1024,
        )
