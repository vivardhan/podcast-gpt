# System Imports
from typing import List

# Third Party Imports
from google.cloud import storage

# Package Imports
from google_client_provider import GoogleClientProvider

def file_exists_gcs(client_provider: GoogleClientProvider, filepath: str) -> bool:
	return client_provider.DATA_BUCKET.blob(filepath).exists()

def upload_to_gcs(client_provider: GoogleClientProvider, filepath: str) -> None:
	print("Uploading to GCS: {}".format(filepath))
	client_provider.DATA_BUCKET.blob(filepath).upload_from_filename(filepath)

def list_files_gcs(client_provider: GoogleClientProvider, prefix: str, extension: str) -> List:
	return [
		f.name for f in client_provider.DATA_BUCKET.list_blobs(prefix=prefix)
		if f.name.endswith(extension)
	]

# Use this for audio files
def download_file_gcs(client_provider: GoogleClientProvider, filepath: str) -> None:
	client_provider.DATA_BUCKET.blob(filepath).download_to_filename(filepath)

def download_textfile_as_string_gcs(client_provider: GoogleClientProvider, filepath: str) -> str:
	tmp_path = "tmp"
	client_provider.DATA_BUCKET.blob(filepath).download_to_filename(tmp_path)
	with open(tmp_path, "r") as f:
		ret = f.read()
		f.close()
		return ret

def upload_string_as_textfile_gcs(client_provider: GoogleClientProvider, filepath: str, string: str) -> None:
	print("Uploading to GCS: {}".format(filepath))
	client_provider.DATA_BUCKET.blob(filepath).upload_from_string(string)

def delete_file_gcs(client_provider: GoogleClientProvider, filepath: str) -> None:
	client_provider.DATA_BUCKET.blob(filepath).delete()