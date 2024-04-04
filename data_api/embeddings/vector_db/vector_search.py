# System Imports
from dataclasses import dataclass
from typing import List

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

class VectorSearch:

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
				chapter_transcript=n.payload[VectorDBConstants.CHAPTER_TRANSCRIPT_FIELD],
			)
			for n in neighbors
		]
