# System Imports
import os
from typing import List
from urllib.request import urlretrieve

# Third Party Imports
import feedparser

# Package Imports
from audio_downloader import DownloadStream, AudioDownloader
from configs import RSSFeedConfig
from data_api.utils.gcs_utils import file_exists_gcs, upload_to_gcs


class RSSAudioDownloader(AudioDownloader):

	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		full_path = os.path.join(stream.folder_path, stream.downloaded_name)
		print("Downloading {}".format(stream.downloaded_name))
		urlretrieve(stream.url, full_path)
		upload_to_gcs(self.gc_provider, full_path)

	def find_audios_to_download(self, config: RSSFeedConfig) -> List[DownloadStream]:
		files_to_download = []

		feed = feedparser.parse(config.url)
		print("Checking {} RSS entries ... ".format(len(feed.entries)))

		for entry in feed.entries:
			for link in entry.links:
				if config.audio_extension in link.href:
					file_name = "{}.{}".format(entry.title.replace('/', ''), config.audio_extension)
					if any([f in file_name for f in config.filter_out]):
						continue

					if not file_exists_gcs(self.gc_provider, os.path.join(self.audio_folder, file_name)):
						files_to_download.append(
							DownloadStream(
								url=link.href, 
								folder_path=self.audio_folder, 
								downloaded_name=file_name,
							)
						)

					break

		return files_to_download
