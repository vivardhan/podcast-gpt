# System Imports
import abc
from dataclasses import dataclass
import os
from typing import Any, List, Union

# Package Imports
from configs import AUDIO_DATA_FOLDER, RSSFeedConfig, YoutubeFeedConfig
from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from google_client_provider import GoogleClientProvider


@dataclass
class DownloadStream:
	# Encapsulates information required to download from a stream

	# URL with stream
	url: str

	# The local folder to download to
	folder_path: str

	# The file name to download to
	downloaded_name: str

# Abstract class for AudioDownloaders
class AudioDownloader(metaclass=abc.ABCMeta):
	def __init__(self, name: str, google_client_provider: GoogleClientProvider):
		self.name = name
		self.audio_folder = os.path.join(self.name, AUDIO_DATA_FOLDER)
		self.gc_provider = google_client_provider

	@abc.abstractmethod
	def download_audio_to_gcs(self, item: DownloadStream) -> None:
		pass

	@abc.abstractmethod
	def find_audios_to_download(self, config: Union[YoutubeFeedConfig, RSSFeedConfig]) -> List[DownloadStream]:
		pass

	def download_all_audios(self, config: Union[YoutubeFeedConfig, RSSFeedConfig]) -> None:
		audio_folder = os.path.join(self.name, AUDIO_DATA_FOLDER)
		create_temp_local_directory(audio_folder)

		files_to_download = self.find_audios_to_download(config)

		if len(files_to_download) > 0:
			print("Downloading {} audio files ... ".format(len(files_to_download)))
			for f in files_to_download:
				self.download_audio_to_gcs(f)
		else:
			print("All audio files already uploaded to GCS!")

		delete_temp_local_directory(audio_folder)


