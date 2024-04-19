# System imports
from typing import List

# Package imports
from data_api.utils.youtube_utils import YoutubeUtils

def get_all_videos(channel_id: str) -> List:
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
    response = YoutubeUtils.list_playlists(
        channel_id=channel_id, 
        part="snippet,contentDetails",
    )

    playlist_ids = []
    for item in response["items"]:
        if item["kind"] != "youtube#channel":
            continue

        playlist_ids.append(item["contentDetails"]["relatedPlaylists"]["uploads"])


    # Extract all videos from each playlist ID
    all_videos = []
    for playlist_id in playlist_ids:
        all_videos.extend(
            YoutubeUtils.extract_videos_from_playlist(
                playlist_id=playlist_id, 
                part="snippet,contentDetails",
            )
        )

    return all_videos