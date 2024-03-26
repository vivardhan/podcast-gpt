# System Imports
import json
import os

# Package Imports
from data_api.utils.gcs_utils import (
	download_textfile_as_string_gcs,
    list_files_gcs,
)
from data_api.utils.paths import Paths
from google_client_provider import GoogleClientProvider
from podcasts import PODCASTS

def main():
	gc_provider = GoogleClientProvider()
	for podcast in PODCASTS:
		print("Computing stats for {}".format(podcast.name))
		raw_transcript_folder = Paths.get_raw_transcript_folder(podcast.name)
		text_files = list_files_gcs(gc_provider, raw_transcript_folder, Paths.TXT_EXT)
		total_words = 0
		file_count = 0
		max_file_size = 0
		for t in text_files:
			text = download_textfile_as_string_gcs(gc_provider, t)
			total_words += len(text.split())
			file_count += 1
			max_file_size = max(max_file_size, len(text.split()))

		chapterized_transcript_folder = Paths.get_chapterized_data_folder(podcast.name)
		chapterized_files = list_files_gcs(gc_provider, chapterized_transcript_folder, Paths.JSON_EXT)

		chapters_count = 0
		max_chapter_size = 0
		for cf in chapterized_files:
			chapters = json.loads(download_textfile_as_string_gcs(gc_provider, cf))
			for chapter_title, chapter_content in chapters.items():
				chapters_count += 1
				num_words = len(chapter_content.split())
				max_chapter_size = max(max_chapter_size, num_words)


		print("{} has {} words".format(podcast.name, total_words))
		print("{} has a maximum of {} words in one episode".format(podcast.name, max_file_size))
		print("{} has {} words on an average in each episode".format(podcast.name, total_words/file_count))
		print("{} has a maximum of {} words in one chapter".format(podcast.name, max_chapter_size))
		print("{} has {} words on an average in each chapter".format(podcast.name, total_words/chapters_count))

if __name__ == "__main__":
	main()