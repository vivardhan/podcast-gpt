# System Imports
from dataclasses import dataclass
import json
import numpy as np
import os
from typing import List

# Third Party Imports
from qdrant_client import QdrantClient
from qdrant_client.models import (
	Distance,
	VectorParams,
)
import tiktoken
from tqdm import tqdm

# Package Imports
from data_api.embeddings.embeddings_generator import EmbeddingsGenerator
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

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

def num_tokens_from_string(string: str, encoding_name: str =  "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

class VectorDB:

	qdrant_client = QdrantClient(
	    url="https://f9b5e12e-96e8-4a0d-92e3-154fad93523a.us-east4-0.gcp.cloud.qdrant.io:6333",
	    api_key=os.environ["QDRANT_API_KEY"],
	)

	COLLECTION_NAME = "podcast_gpt_embeddings"
	EMBEDDINGS_DIMENSION = 1536
	PODCAST_TITLE_FIELD = "podcast_title"
	EPISODE_TITLE_FIELD = "episode_title"
	CHAPTER_TITLE_FIELD = "chapter_title"
	CHAPTER_TRANSCRIPT_FIELD = "chapter_transcript"
	EMBEDDINGS_FIELD = "embeddings"
	DATA_FIELD = "data"

	@classmethod
	def generate_and_store_embeddings(cls, podcast_names: List[str]) -> None:
		count_exceeds = 0
		total_chapters = 0

		js = json.loads(GCSClient.download_textfile_as_string(Paths.VECTOR_DB_PATH))	
		embeddings = js[cls.EMBEDDINGS_FIELD]
		data = js[cls.DATA_FIELD]

		searchable_embeddings = set([
			d[cls.PODCAST_TITLE_FIELD] + d[cls.EPISODE_TITLE_FIELD] + d[cls.CHAPTER_TITLE_FIELD]
			for d in data
		])


		for podcast_name in podcast_names:
			chapterized_data_folder = Paths.get_chapterized_data_folder(podcast_name)
			chapterized_files = GCSClient.list_files(chapterized_data_folder, Paths.JSON_EXT)
			print("Generating embeddings for {}".format(podcast_name))
			for chapterized_file in tqdm(chapterized_files):
				text = GCSClient.download_textfile_as_string(chapterized_file)
				chapters = json.loads(text)

				episode_title = Paths.get_title_from_path(chapterized_file)

				for chapter_title, chapter_text in chapters.items():
					if podcast_name + episode_title + chapter_title in searchable_embeddings:
						continue

					full_text = 'Title: {} \n\nTranscript\n: {}'.format(chapter_title, chapter_text)
					token_count = num_tokens_from_string(full_text)
					total_chapters += 1
					if token_count > EmbeddingsGenerator.EMBEDDING_TOKEN_LIMIT:
						count_exceeds += 1
						continue

					embeddings.append(EmbeddingsGenerator.get_embedding(full_text))
					data.append({
							cls.PODCAST_TITLE_FIELD: podcast_name,
							cls.EPISODE_TITLE_FIELD: episode_title,
							cls.CHAPTER_TITLE_FIELD: chapter_title,
							cls.CHAPTER_TRANSCRIPT_FIELD: chapter_text,
					})

		GCSClient.upload_string_as_textfile( 
			Paths.VECTOR_DB_PATH, 
			json.dumps({
				cls.EMBEDDINGS_FIELD: embeddings,
				cls.DATA_FIELD: data,
			}),
		)

		print("{} chapters exceeded token limit out of {}".format(count_exceeds, total_chapters))

	@classmethod
	def create_and_deploy_index_and_endpoint(cls):
		cls.qdrant_client.recreate_collection(
		    collection_name=cls.COLLECTION_NAME,
		    vectors_config=VectorParams(
		    	size=cls.EMBEDDINGS_DIMENSION, 
		    	distance=Distance.COSINE,
		    ),
		)

		database = json.loads(GCSClient.download_textfile_as_string(Paths.VECTOR_DB_PATH))

		cls.qdrant_client.upload_collection(
			collection_name=cls.COLLECTION_NAME,
			vectors=np.array(database[cls.EMBEDDINGS_FIELD]),
			payload=database[cls.DATA_FIELD],
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
