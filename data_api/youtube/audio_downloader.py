# System Imports
import os
from typing import List

# Third Party Imports
import ffmpeg
from google.cloud import storage
import json
from pytube import Stream, YouTube

# Package imports
from google_oauth_credentials import obtain_google_oauth_credentials

# Set the scope to be youtube readonly
scopes = ["https://www.googleapis.com/auth/devstorage.read_write"]
credentials = obtain_google_oauth_credentials(scopes=scopes)

PROJECT_ID = "podcast-gpt-415000"
storage_client = storage.Client(project=PROJECT_ID, credentials=credentials)
bucket = storage_client.get_bucket("podcast_audio_data")

DATA_FOLDER = "data"
YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="
AUDIO_DATA_FOLDER = "audio_data"
FINAL_CODEC = "flac"


def download_audio(folder_path: str, file_name: str, video_url: str) -> None:
	converted_name = "{}.{}".format(file_name, FINAL_CODEC)
	output_file = os.path.join(folder_path, converted_name)
	if os.path.exists(output_file):
		print("skipping")
		return

	yt = YouTube(video_url)
	audio_stream = yt.streams.get_audio_only()
	codec = audio_stream.mime_type.split('/')[-1]
	downloaded_name = "{}.{}".format(file_name, codec)
	print("Downloading {} ...".format(downloaded_name))
	try:
		audio_stream.download(output_path=folder_path, filename=downloaded_name, skip_existing=True, max_retries=3)
	except:
		print('Could not download: {}'.format(file_name))
	else:
		print("Converting to flac")
		try:
			(
				ffmpeg
					.input(os.path.join(folder_path, downloaded_name))
					.output(output_file, acodec=FINAL_CODEC)
					.run(quiet=True)
			)
		except:
			print('Could not convert {} to flac'.format(file_name))
		else:
			blob = bucket.blob(output_file)
			blob.upload_from_filename(output_file)



def download_all_audios(podcast: str) -> None:
	podcast_folder = os.path.join(DATA_FOLDER, podcast)
	audio_folder = os.path.join(podcast_folder, AUDIO_DATA_FOLDER)
	metadata_file = os.path.join(podcast_folder, "metadata.json")
	with open(metadata_file, "r") as f:
		js = json.load(f)
		print("Downloading {} audio files ... ".format(len(js)))
		for item in js:
			video_url = YOUTUBE_PREFIX + item["contentDetails"]["videoId"]
			file_name = item["snippet"]["title"].replace('/', '')
			download_audio(folder_path=audio_folder, file_name=file_name, video_url=video_url)

def main():
	podcasts = [f for f in os.listdir(DATA_FOLDER) if os.path.isdir(os.path.join(DATA_FOLDER, f))]

	for podcast in podcasts:
		download_all_audios(podcast)


if __name__ == "__main__":
    main()