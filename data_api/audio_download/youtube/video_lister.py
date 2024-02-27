# System imports
import json
import os
from typing import List

# Package imports
from google_client_provider import GoogleClientProvider


def get_all_videos(gc_provider: GoogleClientProvider, channel_id: str) -> List:
    """
    Retrieves a list of video metadata items for a given channel_id

    params:
        gc_provider: google client provider for youtube client
        channel_id: The channel_id for which video items are required

    returns:
        A list of video metadata items, one per video on the channel
    """
    print("Retrieving videos for channel_id: {}".format(channel_id))

    # Find all playlist IDs for the provided channel ID
    request = gc_provider.youtube_client.channels().list(
        part="snippet,contentDetails",
        id=channel_id,
    )
    response = request.execute()

    playlist_ids = []
    for item in response["items"]:
        if item["kind"] != "youtube#channel":
            continue

        playlist_ids.append(item["contentDetails"]["relatedPlaylists"]["uploads"])


    # Extract all videos from each playlist ID
    page_token = None
    all_videos = []
    for playlist_id in playlist_ids:
        while True:
            request = gc_provider.youtube_client.playlistItems().list(
                part="snippet,contentDetails",
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