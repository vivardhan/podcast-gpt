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
		print("Computing stats for {}".format(podcast_name))
		raw_transcript_prefix = os.path.join(podcast_name, TEXT_DATA_FOLDER, RAW_TRANSCRIPT_FOLDER)
		text_files = list_files_gcs(gc_provider, raw_transcript_prefix, TXT_EXT)
		total_words = 0
		file_count = 0
		max_file_size = 0
		for t in text_files:
			text = download_textfile_as_string_gcs(gc_provider, t)
			total_words += len(text.split())
			file_count += 1
			max_file_size = max(max_file_size, total_words)
		print("{} has {} words".format(podcast_name, total_words))
		print("{} has a maximum of {} words in one episode".format(podcast_name, max_file_size))
		print("{} has {} words on an average in each episode".format(podcast_name, total_words/file_count))

if __name__ == "__main__":
	main()