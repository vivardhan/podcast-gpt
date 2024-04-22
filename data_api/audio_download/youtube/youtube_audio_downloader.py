# System Imports
import os
from typing import List

# Third Party Imports
from pytube import YouTube
from tqdm import tqdm

# Package imports
from data_api.audio_download.audio_downloader import AudioDownloader, DownloadStream
from data_api.audio_download.youtube.video_lister import get_all_videos
from data_api.utils.gcs_utils import GCSClient
from data_api.utils.paths import Paths

YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="

class YoutubeAudioDownloader(AudioDownloader):
	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		if not GCSClient.file_exists(stream.metadata_path):
			stream.upload_metadata_to_gcs()

		folder, file = os.path.split(stream.audio_path)
		
		if not GCSClient.file_exists(stream.audio_path):
			try:
				print("Downloading {}".format(file))
				yt = YouTube(stream.url)
				audio_stream = yt.streams.get_audio_only()

				codec = audio_stream.mime_type.split('/')[-1]
				assert codec == stream.extension

				audio_stream.download(
					output_path=folder,
					filename=file,
					max_retries=20,
					timeout=200,
				)
			except Exception as e:
				print('Could not download: {}: {}'.format(stream.audio_path, e))
				raise e

			stream.upload_audio_to_gcs()

	def find_audios_to_download(self) -> List[DownloadStream]:
		videos = get_all_videos(self.config.channel_id)

		audio_files = set(GCSClient.list_files(self.audio_folder, self.config.audio_extension))
		metadata_files = set(GCSClient.list_files(self.audio_folder, Paths.JSON_EXT))

		files_to_download = []
		for item in tqdm(videos):
			title = item["snippet"]["title"].replace('/', '')

			if (
				Paths.get_audio_path(self.name, title, self.config.audio_extension) in audio_files and
				Paths.get_metadata_file_path(self.name, title) in metadata_files
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
					DownloadStream(
						podcast_name=self.name,
						url=video_url, 
						folder_path=self.audio_folder, 
						episode_title=title,
						chapters=chapters,
						podcast_guest=guest,
						extension=self.config.audio_extension,
					)
				)

		return files_to_download
