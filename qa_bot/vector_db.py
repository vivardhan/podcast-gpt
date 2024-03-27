# System Imports
from dataclasses import dataclass
import json
import heapq
from operator import itemgetter
from typing import List

# Third Party Imports
import numpy as np

# Package Imports
from data_api.embeddings.embeddings_generator import EmbeddingsGenerator
from data_api.utils.gcs_utils import download_textfile_as_string_gcs
from data_api.utils.paths import Paths
from google_client_provider import GoogleClientProvider

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

class VectorDB:

	def __init__(self, gc_provider: GoogleClientProvider):
		self.gc_provider = gc_provider
		self._db = json.loads(
			download_textfile_as_string_gcs(
				self.gc_provider, 
				Paths.VECTOR_DB_PATH
			)
		)

	def compute_similarity_scores(self, query_string: str) -> List[float]:
		query = EmbeddingsGenerator.get_embedding(query_string)
		return [
			np.dot(query, key)
			for key in self._db[EmbeddingsGenerator.EMBEDDINGS_FIELD]
		]

	def get_topk_matches(self, query_string: str, k: int) -> List[DatabaseMatch]:
		similarity_scores = self.compute_similarity_scores(query_string)
		indices = range(len(similarity_scores))
		topk = heapq.nlargest(k, zip(indices, similarity_scores), key=itemgetter(1))

		return [
			DatabaseMatch(
				score=score, 
				podcast_title=self._db[EmbeddingsGenerator.PODCAST_TITLE_FIELD][index],
				episode_title=self._db[EmbeddingsGenerator.EPISODE_TITLE_FIELD][index], 
				chapter_title=self._db[EmbeddingsGenerator.CHAPTER_TITLE_FIELD][index],
			)
			for index, score in topk
		]