# System Imports
import json
import os
import re
from typing import List, Tuple
from urllib.request import urlretrieve

# Third Party Imports
import feedparser
from lxml.html import fragments_fromstring, HtmlElement

# Package Imports
from data_api.audio_download.audio_downloader import DownloadStream, AudioDownloader
from configs import RSSFeedConfig
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
		fragments = fragments_fromstring(description)

		# Search for the element with the list of chapters
		for index, fragment in enumerate(fragments):
			# This is specific to 'The Drive' Podcast
			if (type(fragment) != HtmlElement):
				continue

			# This is specific to 'The Drive' Podcast
			if fragment.tag == 'ul':
				chapters_list = [
					item.text_content() 
					for item in fragment.getchildren()
				]

				# Look for a text description followed by a timestamp in brackets [] and a semicolon
				pattern = '(.*?\[)(.*?];)'
				chapters = []
				for c in chapters_list:
					matches = re.findall(pattern, c)

					# If there is no pattern match, don't use this chapter
					if len(matches) == 0:
						continue

					# If there is a pattern match, there is only one match expected
					match = matches[0]

					chapters.append(
						(
							# The timestamp is the 2nd group 
							# Discard the closing bracket and semicolon
							match[1][:-2],
							# The description is the 1st group
							# Discard the open bracket and strip any whitespace
							match[0][:-1].strip()
						)
					)

				return chapters

		return None



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
					
					if any([f in file_name for f in config.filter_out]):
						continue

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
