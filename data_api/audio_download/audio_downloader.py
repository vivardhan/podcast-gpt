# System Imports
import abc
from dataclasses import dataclass
import json
from typing import Any, Dict, List, Optional, Tuple, Union

# Third Party Imports
from openai import OpenAI

# Package Imports
from data_api.audio_download.feed_config import (
    RSSFeedConfig,
    YoutubeFeedConfig,
)
from data_api.utils.file_utils import (
    create_temp_local_directory,
    delete_temp_local_directory,
)
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.parallel_utils import ParallelProcessExecutor
from data_api.utils.paths import Paths


class MetadataKeys:
    CHAPTERS_KEY = "chapters"
    GUEST_KEY = "guest"
    URL_KEY = "url"


@dataclass
class EpisodeMetadata:
    # Encapsulates metadata for an episode

    # The episode title
    title: str

    # URL with audio stream
    url: str

    # Information about chapters in the episode
    # Each element of the list is a pair with timestamp and chapter name
    # Timestamps are formatted as "hh:mm:ss" where truncation is possible, eg:
    # "03:23:45"
    # "00:02:30"
    # "2:30" (2 minutes, 30 seconds)
    chapters: List[Tuple[str, str]]

    # Podcast guest
    podcast_guest: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            MetadataKeys.GUEST_KEY: self.podcast_guest,
            MetadataKeys.URL_KEY: self.url,
            MetadataKeys.CHAPTERS_KEY: self.chapters,
        }


# Abstract class for AudioDownloaders
class AudioDownloader(metaclass=abc.ABCMeta):

    openai_client = OpenAI()
    model_version = "gpt-4-0125-preview"

    def __init__(self, name: str, config: Union[YoutubeFeedConfig, RSSFeedConfig]):
        self.name = name
        self.config = config
        self.audio_folder = Paths.get_audio_data_folder(name)

    @abc.abstractmethod
    def download_audio_to_gcs(self, item: EpisodeMetadata) -> None:
        pass

    @abc.abstractmethod
    def find_audios_to_download(self) -> List[EpisodeMetadata]:
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
		""".format(
            no_guest_response, title
        )
        response = (
            cls.openai_client.chat.completions.create(
                model=cls.model_version,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            .choices[0]
            .message.content
        )

        return None if response == no_guest_response else response

    def download_all_audios(self) -> List[EpisodeMetadata]:
        create_temp_local_directory(self.audio_folder)

        files_to_download = self.find_audios_to_download()

        print("Downloading {} audio files ... ".format(len(files_to_download)))
        ParallelProcessExecutor.run(self.download_audio_to_gcs, files_to_download)

        delete_temp_local_directory(self.audio_folder)

        return files_to_download

    def upload_metadata_to_gcs(self, episode_metadata: EpisodeMetadata) -> None:
        GCSClient.upload_string_as_textfile(
            Paths.get_metadata_file_path(self.name, episode_metadata.title),
            json.dumps(episode_metadata.to_dict()),
        )

    def upload_audio_to_gcs(self, episode_metadata: EpisodeMetadata) -> None:
        GCSClient.upload_file(
            Paths.get_audio_path(
                self.name,
                episode_metadata.title,
                self.config.audio_extension,
            )
        )
