# System Imports
from dataclasses import dataclass
from enum import Enum
import json
import heapq
import numpy as np
from operator import itemgetter
import os
from typing import List

# Third Party Imports
from qdrant_client import QdrantClient
from qdrant_client.models import (
	Distance,
	VectorParams,
)
from tqdm import tqdm

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

	# The chapter transcript
	chapter_transcript: str

class VectorDB:

	qdrant_client = QdrantClient(
	    url="https://f9b5e12e-96e8-4a0d-92e3-154fad93523a.us-east4-0.gcp.cloud.qdrant.io:6333",
	    api_key=os.environ["QDRANT_API_KEY"],
	)

	COLLECTION_NAME = "podcast_gpt_embeddings"
	EMBEDDINGS_DIMENSION = 1536
	K_NEAREST_NEIBHORS = 4
	PODCAST_TITLE_FIELD = "podcast_title"
	EPISODE_TITLE_FIELD = "episode_title"
	CHAPTER_TITLE_FIELD = "chapter_title"
	CHAPTER_TRANSCRIPT_FIELD = "chapter_transcript"
	EMBEDDINGS_FIELD = "embeddings"
	DATA_FIELD = "data"

	def __init__(self, gc_provider: GoogleClientProvider):
		self.gc_provider = gc_provider

	def generate_and_store_embeddings(self, podcast_names: List[str]) -> None:
		count_exceeds = 0
		total_chapters = 0
		vector_id = 0

		embeddings = []
		data = []

		for podcast_name in podcast_names:
			chapterized_data_folder = Paths.get_chapterized_data_folder(podcast_name)
			chapterized_files = list_files_gcs(self.gc_provider, chapterized_data_folder, Paths.JSON_EXT)
			print("Generating embeddings for {}".format(podcast_name))
			for chapterized_file in tqdm(chapterized_files):
				text = download_textfile_as_string_gcs(self.gc_provider, chapterized_file)
				chapters = json.loads(text)

				episode_title = Paths.get_title_from_path(chapterized_file)

				for chapter_title, chapter_text in chapters.items():
					full_text = 'Title: {} \n\nTranscript\n: {}'.format(chapter_title, chapter_text)
					token_count = num_tokens_from_string(full_text)
					total_chapters += 1
					if token_count > EmbeddingsGenerator.EMBEDDING_TOKEN_LIMIT:
						count_exceeds += 1
						continue

					embeddings.append(EmbeddingsGenerator.get_embedding(full_text))
					data.append({
							self.PODCAST_TITLE_FIELD: podcast_name,
							self.EPISODE_TITLE_FIELD: episode_title,
							self.CHAPTER_TITLE_FIELD: chapter_title,
							self.CHAPTER_TRANSCRIPT_FIELD: chapter_text,
					})

					vector_id += 1

		upload_string_as_textfile_gcs(
			self.gc_provider, 
			Paths.VECTOR_DB_PATH, 
			json.dumps({
				self.EMBEDDINGS_FIELD: embeddings,
				self.DATA_FIELD: data,
			}),
		)

		print("{} chapters exceeded token limit out of {}".format(count_exceeds, total_chapters))

	def create_and_deploy_index_and_endpoint(self):
		self.qdrant_client.recreate_collection(
		    collection_name=self.COLLECTION_NAME,
		    vectors_config=VectorParams(
		    	size=self.EMBEDDINGS_DIMENSION, 
		    	distance=Distance.COSINE,
		    ),
		)

		database = json.loads(
			download_textfile_as_string_gcs(
				self.gc_provider, 
				Paths.VECTOR_DB_PATH
			)
		)

		self.qdrant_client.upload_collection(
			collection_name=self.COLLECTION_NAME,
			vectors=np.array(database[EmbeddingsGenerator.EMBEDDINGS_FIELD]),
			payload=database[EmbeddingsGenerator.DATA_FIELD],
		)

	def get_topk_matches(self, query_string: str, k: int) -> List[DatabaseMatch]:
		query = EmbeddingsGenerator.get_embedding(query_string)
		neighbors = self.qdrant_client.search(
			collection_name=self.COLLECTION_NAME,
			query_vector=query,
			limit=k,
		)

		return [
			DatabaseMatch(
				score=n.score,
				podcast_title=n.payload[EmbeddingsGenerator.PODCAST_TITLE_FIELD],
				episode_title=n.payload[EmbeddingsGenerator.EPISODE_TITLE_FIELD],
				chapter_title=n.payload[EmbeddingsGenerator.CHAPTER_TITLE_FIELD],
				chapter_transcript=n.payload[EmbeddingsGenerator.CHAPTER_TRANSCRIPT_FIELD],
			)
			for n in neighbors
		]
