# System Imports
import json
from typing import Dict, List

# Third Party Imports
from openai import OpenAI
import tiktoken
from tqdm import tqdm

# Package Imports
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
	list_files_gcs,
	upload_string_as_textfile_gcs,
)
from data_api.utils.paths import Paths
from google_client_provider import GoogleClientProvider
from podcasts import PODCASTS

def num_tokens_from_string(string: str, encoding_name: str =  "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

class EmbeddingsGenerator:

	client = OpenAI()
	EMBEDDING_TOKEN_LIMIT = 8191
	EMBEDDINGS_MODEL = "text-embedding-3-small"
	PODCAST_TITLE_FIELD = "podcast_title"
	EPISODE_TITLE_FIELD = "episode_title"
	CHAPTER_TITLE_FIELD = "chapter_title"
	EMBEDDINGS_FIELD = "embeddings"

	def __init__(self, gc_provider: GoogleClientProvider):
		self.gc_provider = gc_provider

	@classmethod
	def get_embedding(cls, transcript: str) -> List[float]:
		return cls.client.embeddings.create(
			input=[transcript],
			model=cls.EMBEDDINGS_MODEL,
		).data[0].embedding


	def generate_and_store_embeddings(self) -> Dict:
		podcast_titles = []
		episode_titles = []
		chapter_titles = []
		embeddings = []

		count_exceeds = 0
		total_chapters = 0

		for podcast in PODCASTS:
			chapterized_data_folder = Paths.get_chapterized_data_folder(podcast.name)
			chapterized_files = list_files_gcs(self.gc_provider, chapterized_data_folder, Paths.JSON_EXT)
			print("Generating embeddings for {}".format(podcast.name))
			for chapterized_file in tqdm(chapterized_files):
				text = download_textfile_as_string_gcs(self.gc_provider, chapterized_file)
				chapters = json.loads(text)

				episode_title = Paths.get_title_from_path(chapterized_file)

				for chapter_title, chapter_text in chapters.items():
					full_text = 'Title: {} \n\nTranscript\n: {}'.format(chapter_title, chapter_text)
					token_count = num_tokens_from_string(full_text)
					total_chapters += 1
					if token_count > self.EMBEDDING_TOKEN_LIMIT:
						count_exceeds += 1
						continue

					podcast_titles.append(podcast_title)
					episode_titles.append(episode_title)
					chapter_titles.append(chapter_title)
					embeddings.append(self.get_embedding(full_text))

		
		print("{} chapters exceeded token limit out of {}".format(count_exceeds, total_chapters))

		vector_db = {
			self.PODCAST_TITLE_FIELD: podcast_titles,
			self.EPISODE_TITLE_FIELD: episode_titles,
			self.CHAPTER_TITLE_FIELD: chapter_titles,
			self.EMBEDDINGS_FIELD: embeddings,
		}
		upload_string_as_textfile_gcs(self.gc_provider, Paths.VECTOR_DB_PATH, json.dumps(vector_db))
		return vector_db


