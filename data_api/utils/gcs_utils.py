# System Imports
from typing import List

# Third Party Imports
from google.cloud import storage

# Package Imports
from google_client_provider import GoogleClientProvider

class GCSClient:

	client_provider = GoogleClientProvider()

	@classmethod
	def file_exists(cls, filepath: str) -> bool:
		return cls.client_provider.DATA_BUCKET.blob(filepath).exists()

	@classmethod
	def upload_file(cls, filepath: str) -> None:
		print("Uploading to GCS: {}".format(filepath))
		cls.client_provider.DATA_BUCKET.blob(filepath).upload_from_filename(filepath)

	@classmethod
	def list_files(cls, prefix: str, extension: str) -> List[str]:
		return [
			f.name for f in cls.client_provider.DATA_BUCKET.list_blobs(prefix=prefix)
			if f.name.endswith(extension)
		]

	# Use this for audio files
	@classmethod
	def download_file(cls, filepath: str) -> None:
		cls.client_provider.DATA_BUCKET.blob(filepath).download_to_filename(filepath)

	@classmethod
	def download_textfile_as_string(cls, filepath: str) -> str:
		return cls.client_provider.DATA_BUCKET.blob(filepath).download_as_text()

	@classmethod
	def upload_string_as_textfile(cls, filepath: str, string: str) -> None:
		print("Uploading to GCS: {}".format(filepath))
		cls.client_provider.DATA_BUCKET.blob(filepath).upload_from_string(string)

	@classmethod
	def delete_file(cls, filepath: str) -> None:
		cls.client_provider.DATA_BUCKET.blob(filepath).delete()