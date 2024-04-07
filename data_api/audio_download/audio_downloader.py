# System Imports
import abc
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
import json
import os
from typing import List, Optional, Tuple, Union

# Third Party Imports
from openai import OpenAI

# Package Imports
from data_api.audio_download.feed_config import (
	RSSFeedConfig, 
	YoutubeFeedConfig,
)
from data_api.utils.file_utils import create_temp_local_directory, delete_temp_local_directory
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

class MetadataKeys:
	CHAPTERS_KEY = "chapters"
	GUEST_KEY = "guest"
	URL_KEY = "url"

@dataclass
class DownloadStream:
	# Encapsulates information required to download from an audio stream

	# Name of the podcast
	podcast_name: str

	# URL with stream
	url: str

	# The local folder to download to
	folder_path: str

	# The episode title
	episode_title: str

	# Information about chapters in the audio
	# Each element of the list is a pair with timestamp and chapter name
	# Timestamps are formatted as "hh:mm:ss" where truncation is possible, eg:
	# "03:23:45"
	# "00:02:30"
	# "2:30" (2 minutes, 30 seconds)
	chapters: List[Tuple[str, str]]

	# Podcast guest
	podcast_guest: Optional[str]

	# The audio extension
	extension: str

	# The audio file path
	audio_path: str = field(init=False)

	# The metadata file path
	metadata_path: str = field(init=False)

	def __post_init__(self):
		self.audio_path = Paths.get_audio_path(self.podcast_name, self.episode_title, self.extension)
		self.metadata_path = Paths.get_metadata_file_path(self.podcast_name, self.episode_title)

	def upload_metadata_to_gcs(self) -> None:
		GCSClient.upload_string_as_textfile(
			self.metadata_path,
			json.dumps({
				MetadataKeys.GUEST_KEY: self.podcast_guest,
				MetadataKeys.URL_KEY: self.url,
				MetadataKeys.CHAPTERS_KEY: self.chapters,
			}),
		)

	def upload_audio_to_gcs(self) -> None:
		GCSClient.upload_file(self.audio_path)


# Abstract class for AudioDownloaders
class AudioDownloader(metaclass=abc.ABCMeta):

	openai_client = OpenAI()
	model_version = "gpt-4-0125-preview"

	def __init__(self, name: str, config: Union[YoutubeFeedConfig, RSSFeedConfig]):
		self.name = name
		self.config = config
		self.audio_folder = Paths.get_audio_data_folder(name)

	@abc.abstractmethod
	def download_audio_to_gcs(self, item: DownloadStream) -> None:
		pass

	@abc.abstractmethod
	def find_audios_to_download(self) -> List[DownloadStream]:
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

	@classmethod
	def extract_guest(cls, title: str) -> Optional[str]:
		"""
		Extracts the name of the guest on a podcast episode, if one was present

		params:
			title:
				The podcast episode titles

		returns:
			The name of the guest if there was one, and None otherwise
		"""
		no_guest_response = "No guest"
		prompt = """
		Extract the full name of the guest that appears in the given podcast episode title.
		If no guest name appears, respond with {}.
		If there is a guest, respond with just the name.

		Example 1:
		Podcast Episode Title:
		How Meditation Works & Science-Based Effective Meditations | Huberman Lab Podcast #96
		Guest Name:
		No guest

		Example 2:
		Podcast Episode Title:
		David Goggins: How to Build Immense Inner Strength
		Guest Name:
		David Goggins

		Example 3:
		Podcast Episode Title:
		High-intensity interval training: benefits, risks, protocols, and impact on longevity
		Guest Name:
		No guest

		Example 4:
		Podcast Episode Title:
		#290 ‒ Liquid biopsies for early cancer detection, the role of epigenetics in aging, and the future of aging research | Alex Aravanis, M.D., Ph.D. 
		Guest Name:
		Alex Aravanis

		Podcast Episode Title:
		{}
		Guest Name:
		""".format(no_guest_response, title)
		response = cls.openai_client.chat.completions.create(
			model = cls.model_version,
  			messages=[
  				{"role": "system", "content": "You are a helpful assistant."},
  				{"role": "user", "content": prompt},
  			],
		).choices[0].message.content

		return None if response == no_guest_response else response

	def download_all_audios(self) -> List[DownloadStream]:
		create_temp_local_directory(self.audio_folder)

		files_to_download = self.find_audios_to_download()
		
		print("Downloading {} audio files ... ".format(len(files_to_download)))
		with ProcessPoolExecutor() as executor:
			executor.map(self.download_audio_to_gcs, files_to_download)

		delete_temp_local_directory(self.audio_folder)

		return files_to_download
