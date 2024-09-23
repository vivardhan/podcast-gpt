# System Imports
import os
import requests
from typing import List

# Third Party Imports
import feedparser
from tqdm import tqdm

# Package Imports
from data_api.audio_download.audio_downloader import (
    AudioDownloader,
    EpisodeMetadata,
)
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths


class RSSAudioDownloader(AudioDownloader):

    def download_audio_to_gcs(self, episode_metadata: EpisodeMetadata) -> None:
        metadata_path = Paths.get_metadata_file_path(self.name, episode_metadata.title)
        if not GCSClient.file_exists(metadata_path):
            self.upload_metadata_to_gcs(episode_metadata)

        audio_path = Paths.get_audio_path(
            self.name, episode_metadata.title, self.config.audio_extension
        )
        file = os.path.basename(audio_path)

        if not GCSClient.file_exists(audio_path):
            print("Downloading {}".format(file))
            try:
                r = requests.get(episode_metadata.url)
                with open(audio_path, "wb") as f:
                    f.write(r.content)
            except Exception as e:
                print("Could not download: {}: {}".format(audio_path, e))

            self.upload_audio_to_gcs(episode_metadata)

    def find_audios_to_download(self) -> List[EpisodeMetadata]:
        files_to_download = []

        feed = feedparser.parse(self.config.url)
        print("Checking {} RSS entries ... ".format(len(feed.entries)))

        audio_files = set(
            GCSClient.list_files(self.audio_folder, self.config.audio_extension)
        )
        metadata_files = set(GCSClient.list_files(self.audio_folder, Paths.JSON_EXT))

        for entry in tqdm(feed.entries):
            for link in entry.links:
                if self.config.audio_extension in link.href:
                    title = entry.title.replace("/", "")
                    chapters = self.config.chapter_extractor(entry.content[0].value)

                    if any([f in title for f in self.config.filter_out]):
                        break

                    if (
                        Paths.get_audio_path(
                            self.name, title, self.config.audio_extension
                        )
                        in audio_files
                        and Paths.get_metadata_file_path(self.name, title)
                        in metadata_files
                    ):
                        continue

                    if chapters:
                        guest = self.extract_guest(title)
                        files_to_download.append(
                            EpisodeMetadata(
                                url=link.href,
                                title=title,
                                chapters=chapters,
                                podcast_guest=guest,
                            )
                        )

                    break

        return files_to_download
