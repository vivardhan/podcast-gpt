# Third Party Imports
from google.cloud import storage

# Package Imports
from google_client_provider import GoogleClientProvider

def file_exists_gcs(client_provider: GoogleClientProvider, filepath: str) -> bool:
	return client_provider.DATA_BUCKET.blob(filepath).exists()

def upload_to_gcs(client_provider: GoogleClientProvider, filepath: str) -> None:
	print("Uploading to GCS: {}".format(filepath))
	client_provider.DATA_BUCKET.blob(filepath).upload_from_filename(filepath)
