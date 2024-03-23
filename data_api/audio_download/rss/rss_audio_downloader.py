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
from data_api.audio_download.factory import RSSFeedConfig
from data_api.utils.gcs_utils import (
	file_exists_gcs, 
	upload_string_as_textfile_gcs, 
	upload_to_gcs,
)

class RSSAudioDownloader(AudioDownloader):

	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		if not file_exists_gcs(self.gc_provider, stream.chapters_path):
			upload_string_as_textfile_gcs(self.gc_provider, stream.chapters_path, json.dumps(stream.chapters))

		if not file_exists_gcs(self.gc_provider, stream.audio_path):
			print("Downloading {}".format(stream.downloaded_name))
			urlretrieve(stream.url, stream.audio_path)
			upload_to_gcs(self.gc_provider, stream.audio_path)

	def extract_chapters(self, description: str) -> List[Tuple[str, str]]:
		# See https://stackoverflow.com/questions/8318236/regex-pattern-for-hhmmss-time-string
		# timestamp_pattern = '?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d'

		# The pattern is expected to be a list of <li> </li> tags, with the contained text as follows:
		# "chapter title [hh:mm:ss]"
		# There are some exceptions to this, which are accounted for i.e.:
		# 1. The opening <li> tag might have some additional attributes
		# 2. The square brackets around the timestamp may be parentheses instead
		# 3. There may be some additional text within the brackets containing the timestamp (before or after hh:mm:ss)
		# 4. The timestamp may be truncated, eg. 1:45 or 3:24;17 or 00:1:30 - see the comment above for the pattern
		pattern = '(\<li.*?\>)(.*?[\[|\(].*?)(?:(?:([01]?\d|2[0-3]):)?([0-5]?\d):)?([0-5]?\d)(.*?[\]|\)].*?\<\/li\>)'
		matches = re.findall(pattern, description)

		chapters = []
		for m in matches:
			timestamp = m[4] # seconds
			if not m[3] == '':
				timestamp = m[3] + ':' + timestamp

			if not m[2] == '':
				timestamp = m[2] + ':' + timestamp

			chapters.append(
				(
					timestamp,
					# The description is the 1st group
					# Remove the open bracket and strip whitespace
					m[1][:-1].strip(),
				)
			)

		return chapters

	def find_audios_to_download(self) -> List[DownloadStream]:
		files_to_download = []

		feed = feedparser.parse(self.config.url)
		print("Checking {} RSS entries ... ".format(len(feed.entries)))

		for entry in feed.entries:
			chapters = self.extract_chapters(entry.content[0].value)
			for link in entry.links:
				if self.config.audio_extension in link.href:
					title = entry.title.replace('/', '')
					file_name = "{}.{}".format(title, self.config.audio_extension)
					
					if any([f in file_name for f in self.config.filter_out]):
						break

					if chapters:
						files_to_download.append(
							DownloadStream(
								url=link.href, 
								folder_path=self.audio_folder, 
								downloaded_name=file_name,
								chapters=chapters,
							)
						)

					break

		return files_to_download
