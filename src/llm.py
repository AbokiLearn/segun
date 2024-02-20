# src/llm.py

from sentence_transformers import SentenceTransformer
import torch

from typing import List

from settings import config

encoder = SentenceTransformer(config.EMBEDDING_MODEL)
device = "cuda" if torch.cuda.is_available() else "cpu"


def embed(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    embeddings = encoder.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=batch_size,
        device=device,
    )
    return embeddings.tolist()
