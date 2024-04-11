# System Imports
import os
import re
import requests
from typing import List, Tuple

# Third Party Imports
import feedparser
from tqdm import tqdm

# Package Imports
from data_api.audio_download.audio_downloader import DownloadStream, AudioDownloader
from data_api.audio_download.factory import RSSFeedConfig
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

class RSSAudioDownloader(AudioDownloader):

	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		if not GCSClient.file_exists(stream.metadata_path):
			stream.upload_metadata_to_gcs()

		folder, file = os.path.split(stream.audio_path)
		
		if not GCSClient.file_exists(stream.audio_path):
			print("Downloading {}".format(file))
			try:
				r = requests.get(stream.url)
				with open(stream.audio_path, 'wb') as f:
					f.write(r.content)
			except Exception as e:
				print('Could not download: {}: {}'.format(stream.audio_path, e))

			stream.upload_audio_to_gcs()

	def find_audios_to_download(self) -> List[DownloadStream]:
		files_to_download = []

		feed = feedparser.parse(self.config.url)
		print("Checking {} RSS entries ... ".format(len(feed.entries)))

		audio_files = set(GCSClient.list_files(self.audio_folder, self.config.audio_extension))
		metadata_files = set(GCSClient.list_files(self.audio_folder, Paths.JSON_EXT))

		for entry in tqdm(feed.entries):
			chapters = self.config.chapter_extractor.extract_chapters(entry.content[0].value)
			for link in entry.links:
				if self.config.audio_extension in link.href:
					title = entry.title.replace('/', '')
					
					if any([f in title for f in self.config.filter_out]):
						break

					if (
						Paths.get_audio_path(self.name, title, self.config.audio_extension) in audio_files and
						Paths.get_metadata_file_path(self.name, title) in metadata_files
					):
						continue

					if chapters:
						guest = self.extract_guest(title)
						files_to_download.append(
							DownloadStream(
								podcast_name=self.name,
								url=link.href, 
								folder_path=self.audio_folder,
								episode_title=title,
								chapters=chapters,
								podcast_guest=guest,
								extension=self.config.audio_extension,
							)
						)

					break

		return files_to_download
