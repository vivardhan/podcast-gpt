# System Imports
import abc
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
import os
from typing import List, Tuple, Union

# Package Imports
from configs import (
	AUDIO_DATA_FOLDER,
	CHAPTERS_SUFFIX, 
	JSON_EXT,
	RSSFeedConfig,
	YoutubeFeedConfig,
)
from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from google_client_provider import GoogleClientProvider


@dataclass
class DownloadStream:
	# Encapsulates information required to download from an audio stream

	# URL with stream
	url: str

	# The local folder to download to
	folder_path: str

	# The file name to download audio to
	downloaded_name: str

	# Information about chapters in the audio
	# Each element of the list is a pair with timestamp and chapter name
	# Timestamps are formatted as "hh:mm:ss" where truncation is possible, eg:
	# "03:23:45"
	# "00:02:30"
	# "2:30" (2 minutes, 30 seconds)
	chapters: List[Tuple[str, str]]


	# The remaining fields are path related and should not be initialized
	# They are computed during __post_init__()

	# Path to the downloaded audio file
	audio_path: str = field(init=False)

	# Path to the downloaded chapters file
	chapters_path: str = field(init=False)

	# The audio extension extracted
	extension: str = field(init=False)

	def __post_init__(self):
		self.audio_path = os.path.join(self.folder_path, self.downloaded_name)
		dot_pos = self.downloaded_name.rfind('.')
		file_name = self.downloaded_name[:dot_pos]
		chapters_file = "{}_{}.{}".format(file_name, CHAPTERS_SUFFIX, JSON_EXT)
		self.chapters_path = os.path.join(self.folder_path, chapters_file)
		self.extension = self.downloaded_name[dot_pos + 1:]


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

	@abc.abstractmethod
	def extract_chapters(self, description: str) -> List[Tuple[str, str]]:
		"""
		Given the description of video, extract a list of chapter timestamp and title pairs

		Params:
			description: The text description of the video

		Returns:
			A list of tuples. Each tuple contains a chapter timestamp and title pair, eg:
			[
				("00:00:00", "Introduction"),
				("00:02:40", "Sponsors"),
				...
			]
		"""
		pass

	def download_all_audios(self, config: Union[YoutubeFeedConfig, RSSFeedConfig]) -> None:
		create_temp_local_directory(self.audio_folder)

		files_to_download = self.find_audios_to_download(config)
		
		print("Downloading {} audio files ... ".format(len(files_to_download)))
		with ProcessPoolExecutor() as executor:
			executor.map(self.download_audio_to_gcs, files_to_download)

		delete_temp_local_directory(self.audio_folder)


