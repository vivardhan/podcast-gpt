# System Imports
import os
import re
from typing import List, Optional, Tuple

# Third Party Imports
from pytube import Stream, YouTube

# Package imports
from data_api.audio_download.audio_downloader import AudioDownloader, DownloadStream
from data_api.audio_download.factory import YoutubeFeedConfig
from data_api.audio_download.youtube.video_lister import get_all_videos
from data_api.utils.gcs_utils import file_exists_gcs
from data_api.utils.paths import Paths


YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="

class YoutubeAudioDownloader(AudioDownloader):
	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		if not file_exists_gcs(self.gc_provider, stream.chapters_path):
			stream.upload_metadata_to_gcs(self.gc_provider)
		
		if not file_exists_gcs(self.gc_provider, stream.audio_path):
			try:
				print("Downloading {}".format(stream.downloaded_name))
				yt = YouTube(stream.url)
				audio_stream = yt.streams.get_audio_only()

				codec = audio_stream.mime_type.split('/')[-1]
				assert codec == stream.extension
				audio_stream.download(
					output_path=stream.folder_path, 
					filename=stream.downloaded_name,
					max_retries=20,
					timeout=200,
				)
			except Exception as e:
				print('Could not download: {}: {}'.format(stream.downloaded_name, e))

			stream.upload_audio_to_gcs(self.gc_provider)

	def extract_chapters(self, description: str) -> List[Tuple[str, str]]:
		timestamp_str = '\n\nTimestamps'
		curr_pos = description.find(timestamp_str)
		if curr_pos == -1:
			return None

		pattern = '(\n[0-9][0-9]:[0-5][0-9]:[0-5][0-9] )(.*?\n)'

		curr_pos += len(timestamp_str)
		chapters = re.findall(pattern, description[curr_pos:])

		# Strip away the new line and space characters
		return [(c[0].strip(), c[1].strip()) for c in chapters]

	def find_audios_to_download(self) -> List[DownloadStream]:
		videos = get_all_videos(self.gc_provider, self.config.channel_id)

		files_to_download = []
		for item in videos:
			title = item["snippet"]["title"].replace('/', '')
			downloaded_name = "{}.{}".format(title, self.config.audio_extension)

			if (
				file_exists_gcs(self.gc_provider, os.path.join(self.audio_folder, downloaded_name)) and
				file_exists_gcs(self.gc_provider, os.path.join(self.audio_folder, Paths.get_chapters_file_name_for_title(title)))
			):
				continue


			chapters = self.extract_chapters(item["snippet"]["description"])
			guest = self.extract_guest(title)

			# Only download files that have chapter timestamps since those are the ones
			# that correspond to podcast episodes. Others are likely to be shorts.
			# Note that this logic is specific to Huberman Lab and will require modification
			# for other podcasts that we use YouTube to download.
			if chapters:
				video_url = YOUTUBE_PREFIX + item["contentDetails"]["videoId"]
				files_to_download.append(
					DownloadStream(
						url=video_url, 
						folder_path=self.audio_folder, 
						downloaded_name=downloaded_name,
						chapters=chapters,
						podcast_guest=guest,
					)
				)

		return files_to_download
