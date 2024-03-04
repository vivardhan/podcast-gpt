# System Imports
from dataclasses import dataclass
import os
from typing import List

# Third Party Imports
from pytube import Stream, YouTube

# Package imports
from data_api.audio_download.audio_downloader import AudioDownloader, DownloadStream
from configs import YoutubeFeedConfig
from data_api.utils.gcs_utils import file_exists_gcs, upload_to_gcs
from data_api.audio_download.youtube.video_lister import get_all_videos

YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="

class YoutubeAudioDownloader(AudioDownloader):


	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		yt = YouTube(stream.url)
		audio_stream = yt.streams.get_audio_only()

		codec = audio_stream.mime_type.split('/')[-1]
		extension = stream.downloaded_name[stream.downloaded_name.rfind('.') + 1:]
		assert codec == extension

		print("Downloading {}".format(stream.downloaded_name))
		try:
			audio_stream.download(
				output_path=stream.folder_path, 
				filename=stream.downloaded_name, 
				skip_existing=True, 
				max_retries=3
			)
			upload_to_gcs(self.gc_provider, os.path.join(stream.folder_path, stream.downloaded_name))
		except:
			print('Could not download: {}'.format(stream.downloaded_name))

	def find_audios_to_download(self, config: YoutubeFeedConfig) -> List[DownloadStream]:
		videos = get_all_videos(self.gc_provider, config.channel_id)

		files_to_download = []
		for item in videos:
			file_name = item["snippet"]["title"].replace('/', '')
			downloaded_name = "{}.{}".format(file_name, config.audio_extension)
			if file_exists_gcs(self.gc_provider, os.path.join(self.audio_folder, downloaded_name)):
				continue

			video_url = YOUTUBE_PREFIX + item["contentDetails"]["videoId"]
			files_to_download.append(
				DownloadStream(
					url=video_url, 
					folder_path=self.audio_folder, 
					downloaded_name=downloaded_name,
				)
			)

		return files_to_download
