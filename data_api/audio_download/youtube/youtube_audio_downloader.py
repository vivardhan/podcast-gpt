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
from data_api.utils.gcs_utils import delete_file_gcs, file_exists_gcs, upload_to_gcs, upload_string_as_textfile_gcs
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
			audio_file = os.path.join(self.audio_folder, downloaded_name)

			chapters = self.extract_chapters(item["snippet"]["description"])
			chapters_name = "{}_{}.{}".format(file_name, "chapters", "json")
			chapters_file = os.path.join(self.audio_folder, chapters_name)

			# Only download files that have chapter timestamps since those are the ones
			# that correspond to podcast episodes. Others are likely to be shorts.
			# Note that this logic is specific to Huberman Lab and will require modification
			# for other podcasts that we use YouTube to download.
			if chapters:
				if not file_exists_gcs(self.gc_provider, chapters_file):
					upload_string_as_textfile_gcs(self.gc_provider, chapters_file, json.dumps(chapters))

				if not file_exists_gcs(self.gc_provider, audio_file):
					video_url = YOUTUBE_PREFIX + item["contentDetails"]["videoId"]
					files_to_download.append(
						DownloadStream(
							url=video_url, 
							folder_path=self.audio_folder, 
							downloaded_name=downloaded_name,
						)
					)
			else:
				# If there are no chapters and we mistakenly downloaded the audio file
				# or saved the (empty) chapters file, delete them
				if file_exists_gcs(self.gc_provider, chapters_file):
					delete_file_gcs(self.gc_provider, chapters_file)

				if file_exists_gcs(self.gc_provider, audio_file):
					delete_file_gcs(self.gc_provider, audio_file)

		return files_to_download
