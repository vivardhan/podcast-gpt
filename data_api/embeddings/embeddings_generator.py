# System Imports
from typing import List

# Third Party Imports
from openai import OpenAI


class EmbeddingsGenerator:

    client = OpenAI()
    EMBEDDING_TOKEN_LIMIT = 8191
    EMBEDDINGS_MODEL = "text-embedding-3-small"

    @classmethod
    def get_embedding(cls, transcript: str) -> List[float]:
        return (
            cls.client.embeddings.create(
                input=[transcript],
                model=cls.EMBEDDINGS_MODEL,
            )
            .data[0]
            .embedding
        )
