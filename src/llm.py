# src/llm.py

from sentence_transformers import SentenceTransformer
import torch

from concurrent.futures import ThreadPoolExecutor
import asyncio

from typing import List

from settings import config

executor = ThreadPoolExecutor()
encoder = SentenceTransformer(config.EMBEDDING_MODEL)
device = "cuda" if torch.cuda.is_available() else "cpu"


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
