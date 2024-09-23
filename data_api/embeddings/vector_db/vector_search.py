# System Imports
from dataclasses import dataclass
from typing import List, Optional

# Third Party Imports
from qdrant_client import QdrantClient

# Package Imports
from data_api.embeddings.embeddings_generator import EmbeddingsGenerator
from data_api.embeddings.vector_db.constants import VectorDBConstants
from data_api.embeddings.vector_db.qdrant_client_provider import QdrantClientProvider


@dataclass
class DatabaseMatch:
    """Encapsulates one matched row fron a vector DB"""

    # The cosine similarity match score
    score: float

    # The podcast title
    podcast_title: str

    # The title of the episode where the text comes from
    episode_title: str

    # The chapter title within the episode
    chapter_title: str

    # The chapter transcript
    chapter_transcript: str

    # The episode's media url
    url: str

    # The timestamp in seconds when the chapter starts
    start_timestamp: int

    # The timestamp in seconds when the chapter ends
    # If the end of the chapter is the end of the episode it is None
    end_timestamp: Optional[int]

    # The guest on this episode (can be None)
    guest: Optional[str]

    def to_dict(self):
        return {
            VectorDBConstants.SCORE_FIELD: self.score,
            VectorDBConstants.PODCAST_TITLE_FIELD: VectorSearch.podcast_name_to_title[
                self.podcast_title
            ],
            VectorDBConstants.EPISODE_TITLE_FIELD: self.episode_title,
            VectorDBConstants.CHAPTER_TITLE_FIELD: self.chapter_title,
            VectorDBConstants.EPISODE_URL_FIELD: self.url,
            VectorDBConstants.START_TIMESTAMP_FIELD: self.start_timestamp,
            VectorDBConstants.END_TIMESTAMP_FIELD: self.end_timestamp,
            VectorDBConstants.PODCAST_GUEST_FIELD: self.guest,
        }


class VectorSearch:

    podcast_name_to_title = {
        "hubermanlab": "Huberman Lab Podcast",
        "PeterAttiaMD": "The Peter Attia Drive Podcast",
    }

    @classmethod
    def get_topk_matches(cls, query_string: str, k: int) -> List[DatabaseMatch]:
        query = EmbeddingsGenerator.get_embedding(query_string)
        neighbors = QdrantClientProvider.client.search(
            collection_name=VectorDBConstants.COLLECTION_NAME,
            query_vector=query,
            limit=k,
        )

        return [
            DatabaseMatch(
                score=n.score,
                podcast_title=n.payload[VectorDBConstants.PODCAST_TITLE_FIELD],
                episode_title=n.payload[VectorDBConstants.EPISODE_TITLE_FIELD],
                chapter_title=n.payload[VectorDBConstants.CHAPTER_TITLE_FIELD],
                chapter_transcript=n.payload[
                    VectorDBConstants.CHAPTER_TRANSCRIPT_FIELD
                ],
                url=n.payload[VectorDBConstants.EPISODE_URL_FIELD],
                start_timestamp=n.payload[VectorDBConstants.START_TIMESTAMP_FIELD],
                end_timestamp=n.payload[VectorDBConstants.END_TIMESTAMP_FIELD],
                guest=n.payload[VectorDBConstants.PODCAST_GUEST_FIELD],
            )
            for n in neighbors
        ]
