# System Imports
from typing import Dict, List

# Package Imports
from google_client_provider import GoogleClientProvider

class YoutubeUtils:

	client_provider = GoogleClientProvider()

	@classmethod
	def list_playlists(cls, channel_id: str, part: str) -> Dict:
		request = cls.client_provider.youtube_client.channels().list(
			part="snippet,contentDetails",
			id=channel_id,
		)
		response = request.execute()

		return response

	@classmethod
	def extract_videos_from_playlist(cls, playlist_id: str, part: str) -> List:

		all_videos = []

		page_token = None
		while True:
			request = cls.client_provider.youtube_client.playlistItems().list(
				part=part,
				playlistId=playlist_id,
				maxResults=50,
				pageToken=page_token,
			)

			response = request.execute()
			all_videos.extend(response["items"])

			if "nextPageToken" in response:
				page_token = response["nextPageToken"]
			else:
				break

		return all_videos