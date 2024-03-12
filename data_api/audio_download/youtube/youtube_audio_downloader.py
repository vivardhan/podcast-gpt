# System Imports
import json
import os
import re
from typing import List, Tuple

# Third Party Imports
from pytube import Stream, YouTube

# Package imports
from data_api.audio_download.audio_downloader import AudioDownloader, DownloadStream
from configs import YoutubeFeedConfig
from data_api.utils.gcs_utils import (
	file_exists_gcs, 
	upload_string_as_textfile_gcs,
	upload_to_gcs,
)
from data_api.audio_download.youtube.video_lister import get_all_videos

YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="

class YoutubeAudioDownloader(AudioDownloader):


	def download_audio_to_gcs(self, stream: DownloadStream) -> None:
		if not file_exists_gcs(self.gc_provider, stream.chapters_path):
			upload_string_as_textfile_gcs(self.gc_provider, stream.chapters_path, json.dumps(stream.chapters))
		
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
				upload_to_gcs(self.gc_provider, stream.audio_path)
			except Exception as e:
				print('Could not download: {}: {}'.format(stream.downloaded_name, e))

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

	def find_audios_to_download(self, config: YoutubeFeedConfig) -> List[DownloadStream]:
		videos = get_all_videos(self.gc_provider, config.channel_id)

		files_to_download = []
		for item in videos:
			file_name = item["snippet"]["title"].replace('/', '')
			downloaded_name = "{}.{}".format(file_name, config.audio_extension)

			chapters = self.extract_chapters(item["snippet"]["description"])

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
					)
				)

		return files_to_download
