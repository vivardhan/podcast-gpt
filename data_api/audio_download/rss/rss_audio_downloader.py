# System Imports
import json
import os
import re
from typing import List, Tuple
from urllib.request import urlretrieve

# Third Party Imports
import feedparser

# Package Imports
from data_api.audio_download.audio_downloader import DownloadStream, AudioDownloader
from configs import RSSFeedConfig
from data_api.utils.gcs_utils import (
	delete_file_gcs, 
	file_exists_gcs, 
	upload_string_as_textfile_gcs, 
	upload_to_gcs,
)


class RSSAudioDownloader(AudioDownloader):

	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		full_path = os.path.join(stream.folder_path, stream.downloaded_name)
		print("Downloading {}".format(stream.downloaded_name))
		urlretrieve(stream.url, full_path)
		upload_to_gcs(self.gc_provider, full_path)

	def extract_chapters(self, description: str) -> List[Tuple[str, str]]:
		chapters_list_str = '\<p\>We discuss\:\<\/p\> \<ul.*?\>'
		list_start_match = re.search(chapters_list_str, description)

		if not list_start_match:
			return None

		start_pos = list_start_match.end()

		pattern = '( \<li\>)(.*?)(\[.*?\];)(\<\/li\>)'
		matches = re.findall(pattern, description[start_pos:])

		return [
			# Based on the regex pattern, there are 4 groups in each chapter match:
			# 0. Open list item html tag (<li>)
			# 1. The chapter text description
			# 2. The timestamp ([hh:mm:ss];) - hh:mm:ss could be truncated, eg. 2:45 or 3:23:24
			# 3. Close list item html tag (</li>)
			#
			# Discard 0 and 3 above.
			# Eliminate the opening '[' and closing '];' to get timestamp
			# Strip any leading and trailing whitespace to get title
			(m[2][1:-2], m[1].strip())
			for m in matches
		]

	def find_audios_to_download(self, config: RSSFeedConfig) -> List[DownloadStream]:
		files_to_download = []

		feed = feedparser.parse(config.url)
		print("Checking {} RSS entries ... ".format(len(feed.entries)))

		for entry in feed.entries:
			chapters = self.extract_chapters(entry.content[0].value)
			for link in entry.links:
				if config.audio_extension in link.href:
					title = entry.title.replace('/', '')
					file_name = "{}.{}".format(title, config.audio_extension)
					audio_file = os.path.join(self.audio_folder, file_name)
					if any([f in file_name for f in config.filter_out]):
						continue

					chapters_name = "{}_{}.{}".format(title, "chapters", "json")
					chapters_file = os.path.join(self.audio_folder, chapters_name)

					# Only download files that have chapter timestamps since those are the ones
					# that correspond to podcast episodes. Others are likely to be shorts.
					# Note that this logic is specific to Huberman Lab and will require modification
					# for other podcasts that we use YouTube to download.
					if chapters:
						if not file_exists_gcs(self.gc_provider, chapters_file):
							upload_string_as_textfile_gcs(self.gc_provider, chapters_file, json.dumps(chapters))

						if not file_exists_gcs(self.gc_provider, audio_file):
							files_to_download.append(
								DownloadStream(
									url=link.href, 
									folder_path=self.audio_folder, 
									downloaded_name=file_name,
								)
							)
					else:
						# If there are no chapters and we mistakenly downloaded the audio file
						# or saved the (empty) chapters file, delete them
						if file_exists_gcs(self.gc_provider, chapters_file):
							delete_file_gcs(self.gc_provider, chapters_file)

						if file_exists_gcs(self.gc_provider, audio_file):
							delete_file_gcs(self.gc_provider, audio_file)

					break

		return files_to_download
