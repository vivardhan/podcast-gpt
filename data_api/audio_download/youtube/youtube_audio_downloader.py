# System Imports
import os
from typing import List

# Third Party Imports
from pytube import YouTube
from tqdm import tqdm

# Package imports
from data_api.audio_download.audio_downloader import (
    AudioDownloader,
    EpisodeMetadata,
)
from data_api.audio_download.youtube.video_lister import get_all_videos
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="


class YoutubeAudioDownloader(AudioDownloader):
    def download_audio_to_gcs(self, episode_metadata: EpisodeMetadata) -> None:
        metadata_path = Paths.get_metadata_file_path(self.name, episode_metadata.title)
        if not GCSClient.file_exists(metadata_path):
            self.upload_metadata_to_gcs(episode_metadata)

        audio_path = Paths.get_audio_path(
            self.name, episode_metadata.title, self.config.audio_extension
        )
        folder, file = os.path.split(audio_path)

        if not GCSClient.file_exists(audio_path):
            try:
                print("Downloading {}".format(file))
                yt = YouTube(episode_metadata.url + ".")
                audio_stream = yt.streams.get_audio_only()

                codec = audio_stream.mime_type.split("/")[-1]
                assert codec == self.config.audio_extension

                audio_stream.download(
                    output_path=folder,
                    filename=file,
                    max_retries=20,
                    timeout=200,
                )
            except Exception as e:
                print("Could not download: {}: {}".format(audio_path, e))
                raise e

            self.upload_audio_to_gcs(episode_metadata)

    def find_audios_to_download(self) -> List[EpisodeMetadata]:
        videos = get_all_videos(self.config.channel_id)

        audio_files = set(
            GCSClient.list_files(self.audio_folder, self.config.audio_extension)
        )
        metadata_files = set(GCSClient.list_files(self.audio_folder, Paths.JSON_EXT))

        files_to_download = []
        for item in tqdm(videos):
            title = item["snippet"]["title"].replace("/", "")

            if (
                Paths.get_audio_path(self.name, title, self.config.audio_extension)
                in audio_files
                and Paths.get_metadata_file_path(self.name, title) in metadata_files
            ):
                continue

            chapters = self.config.chapter_extractor(item["snippet"]["description"])

            # Only download files that have chapter timestamps since those are the ones
            # that correspond to podcast episodes. Others are likely to be shorts.
            # Note that this logic is specific to Huberman Lab and will require modification
            # for other podcasts that we use YouTube to download.
            if chapters:
                guest = self.extract_guest(title)
                video_url = YOUTUBE_PREFIX + item["contentDetails"]["videoId"]
                files_to_download.append(
                    EpisodeMetadata(
                        url=video_url,
                        title=title,
                        chapters=chapters,
                        podcast_guest=guest,
                    )
                )

        return files_to_download
