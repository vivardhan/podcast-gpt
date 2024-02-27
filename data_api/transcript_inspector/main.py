# System Imports
import os

# Package Imports
from configs import (
	podcast_configs, 
	RAW_TRANSCRIPT_FOLDER,
	TEXT_DATA_FOLDER,
	TXT_EXT,
)
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
    list_files_gcs,
)
from google_client_provider import GoogleClientProvider

def main():
	gc_provider = GoogleClientProvider()
	for podcast_name, config in podcast_configs.items():
		raw_transcript_prefix = os.path.join(podcast_name, TEXT_DATA_FOLDER, RAW_TRANSCRIPT_FOLDER)
		text_files = list_files_gcs(gc_provider, raw_transcript_prefix, TXT_EXT)
		total_words = 0
		for t in text_files:
			text = download_textfile_as_string_gcs(gc_provider, t)
			total_words += len(text.split())

		print("{} has {} words".format(podcast_name, total_words))

if __name__ == "__main__":
	main()