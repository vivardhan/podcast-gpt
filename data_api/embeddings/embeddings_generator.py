# System Imports
from typing import List

# Third Party Imports
from openai import OpenAI
import tiktoken

def num_tokens_from_string(string: str, encoding_name: str =  "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

class EmbeddingsGenerator:

	client = OpenAI()
	EMBEDDING_TOKEN_LIMIT = 8191
	EMBEDDINGS_MODEL = "text-embedding-3-small"

	@classmethod
	def get_embedding(cls, transcript: str) -> List[float]:
		return cls.client.embeddings.create(
			input=[transcript],
			model=cls.EMBEDDINGS_MODEL,
		).data[0].embedding
